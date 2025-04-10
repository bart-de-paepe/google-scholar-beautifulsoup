import pika
from bson import ObjectId

from requests import HTTPError, Timeout

class RabbitMQService:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))
        self.channel = self.connection.channel()

    def post(self, exchange, routing_key, body, logging_service):
        self.channel.queue_declare(queue=routing_key, durable=True)
        self.channel.basic_publish(exchange=exchange, routing_key=routing_key, body=body, properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent))
        logging_service.logger.debug(f" [x] Sent '{routing_key} {body}'")
        print(f" [x] Sent '{routing_key} {body}'")

    def close(self):
        self.connection.close()

    def generate_callback_parse_email_body(self, email_service, parse_service, logging_service):
        def callback(ch, method, properties, body):
            try:
                logging_service.logger.debug(f" [x] Received parse '{body}'")
                print(f" [x] Received parse {body}")
                hex_string = body.decode('utf-8')
                email_id = ObjectId(hex_string)
                email_body = parse_service.get_body(email_id)
                try:
                    parse_service.parse_body(email_id, email_body)
                    # flag the email as processed
                    email_update_where = {
                        "_id": email_id,
                    }
                    current_email = email_service.get_current_email(email_id)
                    current_email.is_processed = True
                    email_update_what = {
                        "updated_at": current_email.get_updated_at_formatted(),
                        "is_processed": current_email.is_processed,
                        "body": {
                            "text_html": email_body.text_html,
                            "is_parsed": email_body.is_parsed,
                            "is_google_scholar_format": email_body.is_google_scholar_format,
                            "log_message": email_body.log_message,
                        }
                    }
                    email_service.update_email(email_update_what, email_update_where)
                except IndexError as error:
                    index, log_message, is_parsed, is_google_scholar_format = error.args
                    email_update_where = {
                        "_id": email_id,
                    }
                    current_email = email_service.get_current_email(email_id)
                    current_email.is_processed = True
                    email_update_what = {
                        "updated_at": current_email.get_updated_at_formatted(),
                        "is_processed": current_email.is_processed,
                        "body": {
                            "text_html": email_body.text_html,
                            "is_parsed": is_parsed,
                            "is_google_scholar_format": is_google_scholar_format,
                            "log_message": log_message,
                        }
                    }
                    email_service.update_email(email_update_what, email_update_where)
                    logging_service.logger.debug('Index error: {}'.format(error))
                self.channel.basic_ack(delivery_tag=method.delivery_tag)
            except ConnectionError as error:
                logging_service.logger.debug('Connection error: {}'.format(error))
            except TypeError as error:
                logging_service.logger.debug('Type error: {}'.format(error))

        return callback

    def receive_parse_email_body(self, email_service, parse_service, logging_service):
        callback = self.generate_callback_parse_email_body(email_service, parse_service, logging_service)
        self.channel.queue_declare(queue='parse', durable=True)
        self.channel.basic_consume(queue='parse', on_message_callback=callback)
        logging_service.logger.debug(' [*] Waiting to parse email. To exit press CTRL+C')
        print(' [*] Waiting to parse email. To exit press CTRL+C')
        self.channel.start_consuming()

    def generate_callback_search_doi(self, parse_service, search_doi_service, logging_service):
        def callback(ch, method, properties, body):
            try:
                logging_service.logger.debug(f" [x] Received search doi '{body}'")
                print(f" [x] Received search doi {body}")
                hex_string = body.decode('utf-8')
                object_id = ObjectId(hex_string)
                link_and_media_type = search_doi_service.get_link_and_media_type(object_id)
                link = link_and_media_type['link']
                search_doi_service.set_link(link)
                logging_service.logger.debug(f'link url: {link.url}')
                print(f"Link url: {link.url}")
                logging_service.logger.debug(f'initial state: {search_doi_service.current_state.to_string()}')
                print("initial state: " + search_doi_service.current_state.to_string())
                try:
                    while not link.doi and not search_doi_service.processing_finished():
                        logging_service.logger.debug(f"next step: {search_doi_service.current_state.to_string()}")
                        print("next step: " + search_doi_service.current_state.to_string())
                        link = search_doi_service.next_step(link_and_media_type)
                    # update the link
                    search_doi_service.update_link_content(object_id)
                    # flag the search result as processed
                    search_result_update_where = {
                        "_id": object_id,
                    }
                    current_search_result = parse_service.get_current_search_result(object_id)
                    current_search_result.is_processed = True
                    search_result_update_what = {
                        "updated_at": current_search_result.get_updated_at_formatted(),
                        "is_processed": current_search_result.is_processed,
                    }
                    parse_service.update_search_result(search_result_update_what, search_result_update_where)
                    # reset the state for the next search result
                    search_doi_service.reset_state()
                except HTTPError as error:
                    logging_service.logger.debug('HTTP error: {}'.format(error))
                except Timeout as error:
                    logging_service.logger.debug('Timeout error: {}'.format(error))
                self.channel.basic_ack(delivery_tag=method.delivery_tag)
            except ConnectionError as error:
                logging_service.logger.debug('Connection error: {}'.format(error))

        return callback

    def receive_search_doi(self, parse_service, search_doi_service, logging_service):
        callback = self.generate_callback_search_doi(parse_service, search_doi_service, logging_service)
        self.channel.queue_declare(queue='doi', durable=True)
        self.channel.basic_consume(queue='doi', on_message_callback=callback)
        logging_service.logger.debug(' [*] Waiting to search doi. To exit press CTRL+C')
        print(' [*] Waiting to search doi. To exit press CTRL+C')
        self.channel.start_consuming()

    def generate_callback_crossref(self, parse_service, crossref_service, logging_service):
        def callback(ch, method, properties, body):
            logging_service.logger.debug(f" [x] Received crossref '{body}'")
            print(f" [x] Received crossref {body}")
            hex_string = body.decode('utf-8')
            object_id = ObjectId(hex_string)
            link = crossref_service.get_link(object_id)
            crossref_service.get_crossref(object_id, link)
            # update the link
            # flag the search result as processed
            search_result_update_where = {
                "_id": object_id,
            }
            current_search_result = parse_service.get_current_search_result(object_id)
            current_search_result.link.is_processed = True
            search_result_update_what = {
                "link": {
                    "url": link.url,
                    "location_replace_url": link.location_replace_url,
                    "response_code": link.response_code,
                    "response_type": link.response_type,
                    "is_accepted_type": link.is_accepted_type,
                    "DOI": link.doi,
                    "log_message": link.log_message,
                    "is_DOI_success": link.is_doi_success,
                    "is_processed": current_search_result.link.is_processed
                },
            }
            parse_service.update_search_result(search_result_update_what, search_result_update_where)
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
        return callback

    def receive_crossref(self, parse_service, crossref_service, logging_service):
        callback = self.generate_callback_crossref(parse_service, crossref_service, logging_service)
        self.channel.queue_declare(queue='crossref', durable=True)
        self.channel.basic_consume(queue='crossref', on_message_callback=callback)
        logging_service.logger.debug(' [*] Waiting to lookup Crossref. To exit press CTRL+C')
        print(' [*] Waiting to lookup Crossref. To exit press CTRL+C')
        self.channel.start_consuming()
import os
import sys

import click
from dependency_injector.wiring import Provide, inject

from app.src.app_containers import Container
from app.src.services.crossref_service import CrossrefService
from app.src.services.email_service import EmailService
from app.src.services.logging_service import LoggingService
from app.src.services.parse_service import ParseService
from app.src.services.rabbitmq_service import RabbitMQService
from app.src.services.search_DOI_service import SearchDOIService


@click.group()
def cli():
    # create group for all the commands so you can
    # run them from the __name__ == "__main__" block
    pass

@cli.command()
@inject
def process_unread_emails(
        email_service: EmailService = Provide[Container.email_service],
):    #python -m app.src.main process-unread-emails
    """
        Connects to inbox and gathers unread emails, store contents
        of email(s) into MongoDB.
        """
    try:
        mailbox = email_service.connect_and_login()
        unread_email_ids = email_service.get_unread_ids(mailbox)
        # Exits if there are no new unread emails
        if not unread_email_ids:
            email_service.log('No new unread emails to process.')
            mailbox.close()
            exit()

        for email_id in unread_email_ids:
            email_data = email_service.fetch_email_content(mailbox, email_id)
            dict_current_email = email_service.parse_email(email_data)
            email_service.move_email(dict_current_email['current_email'], mailbox, email_id)
            email_service.add_to_queue(dict_current_email['db_email_id'])

        email_service.close()
        mailbox.expunge()
        mailbox.close()
        mailbox.logout()
    except ConnectionError as error:
        email_service.log('Connection error: {}'.format(error))

@cli.command()
@inject
def process_email_body(
        email_service: EmailService = Provide[Container.email_service],
        parse_service: ParseService = Provide[Container.parse_service],
        logging_service: LoggingService = Provide[Container.logging_service],
        rabbitmq_service: RabbitMQService = Provide[Container.rabbitmq_client],
):  #python -m app.src.main process-email-body
    try:
        rabbitmq_service.receive_parse_email_body(email_service, parse_service, logging_service)
    except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)


@cli.command()
@inject
def process_search_doi(
        parse_service: ParseService = Provide[Container.parse_service],
        search_doi_service: SearchDOIService = Provide[Container.search_DOI_service],
        logging_service: LoggingService = Provide[Container.logging_service],
        rabbitmq_service: RabbitMQService = Provide[Container.rabbitmq_client],
):  #python -m app.src.main process-search-doi
    try:
        rabbitmq_service.receive_search_doi(parse_service, search_doi_service, logging_service)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

@cli.command()
@inject
def process_crossref(
        parse_service: ParseService = Provide[Container.parse_service],
        crossref_service: CrossrefService = Provide[Container.crossref_service],
        logging_service: LoggingService = Provide[Container.logging_service],
        rabbitmq_service: RabbitMQService = Provide[Container.rabbitmq_client],
):  #python -m app.src.main process-crossref
    try:
        rabbitmq_service.receive_crossref(parse_service, crossref_service, logging_service)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__':
    container = Container()
    container.init_resources()
    container.wire(modules=[__name__])
    cli()
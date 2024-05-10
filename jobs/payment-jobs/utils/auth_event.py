
from flask import current_app
from pay_api.models import PaymentAccountModel
from pay_api.services import gcp_queue_publisher
from pay_jobs.services.gcp_queue_publisher import QueueMessage
from pay_api.utils.enums import QueueSources, QueueMessage
from sentry_sdk import capture_message
from typing import Dict

class AuthEvent: 
  """Publishes to the auth queue as an auth event though GCP."""

  @staticmethod
  def publish_lock_account_event(pay_account: PaymentAccountModel, data):
      """Publish payment message to the mailer queue."""
      try:
          payload = AuthEvent._create_event_payload(pay_account, data)
          gcp_queue_publisher.publish_to_queue(
              QueueMessage(
                  source=QueueSources.PAY_QUEUE.value,
                  message_type=QueueMessage.LOCK_ACCOUNT.value,
                  payload=payload,
                  topic=current_app.config.get('AUTH_QUEUE_TOPIC')
              )
          )
      except Exception as e:  # NOQA pylint: disable=broad-except
          current_app.logger.error(e)
          current_app.logger.warning('Notification to Queue failed for the Account %s - %s', pay_account.auth_account_id,
                                  pay_account.name)
          capture_message('Notification to Queue failed for the Account {auth_account_id}, {msg}.'.format(
              auth_account_id=pay_account.auth_account_id, msg=payload), level='error')
              
  @staticmethod
  def _create_event_payload(pay_account, row):
          # grab outstanding and original amount.
          return {
              'accountId': pay_account.auth_account_id,
              'paymentMethod': 'EFT',
              'outstandingAmount': 0, # TODO 
              'originalAmount': 0, # TODO 
              'amount': 0 # TODO
          }

# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests to assure the FeeSchedule Service.

Test-Suite to ensure that the FeeSchedule Service is working as expected.
"""

import uuid
from datetime import datetime

import pytest
from tests import skip_in_pod
from tests.utilities.base_test import (
    factory_invoice, factory_invoice_reference, factory_payment, factory_payment_account, factory_payment_line_item,
    factory_payment_transaction, get_payment_request, get_zero_dollar_payment_request)

from pay_api.exceptions import BusinessException
from pay_api.models import FeeSchedule, Invoice, Payment, PaymentAccount, PaymentLineItem, PaymentTransaction
from pay_api.services.payment_transaction import PaymentTransaction as PaymentTransactionService
from pay_api.utils.enums import Status
from pay_api.utils.errors import Error


def test_transaction_saved_from_new(session):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    payment_transaction = PaymentTransactionService()
    payment_transaction.status_code = 'DRAFT'
    payment_transaction.transaction_end_time = datetime.now()
    payment_transaction.transaction_start_time = datetime.now()
    payment_transaction.pay_system_url = 'http://google.com'
    payment_transaction.client_system_url = 'http://google.com'
    payment_transaction.payment_id = payment.id
    payment_transaction = payment_transaction.save()

    transaction = PaymentTransactionService.find_by_id(payment.id, payment_transaction.id)

    assert transaction is not None
    assert transaction.id is not None
    assert transaction.status_code is not None
    assert transaction.payment_id is not None
    assert transaction.client_system_url is not None
    assert transaction.pay_system_url is not None
    assert transaction.transaction_start_time is not None
    assert transaction.transaction_end_time is not None


def test_transaction_create_from_new(session):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    transaction = PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)

    assert transaction is not None
    assert transaction.id is not None
    assert transaction.status_code is not None
    assert transaction.payment_id is not None
    assert transaction.client_system_url is not None
    assert transaction.pay_system_url is not None
    assert transaction.transaction_start_time is not None
    assert transaction.asdict() is not None


def test_transaction_create_from_invalid_payment(session):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    with pytest.raises(BusinessException) as excinfo:
        PaymentTransactionService.create(999, {
            'clientSystemUrl': '',
            'payReturnUrl': ''
        }, skip_auth_check=True)
    assert excinfo.value.status == Error.PAY005.status
    assert excinfo.value.message == Error.PAY005.message
    assert excinfo.value.code == Error.PAY005.name


@skip_in_pod
def test_transaction_update(session, stan_server):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    transaction = PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)
    transaction = PaymentTransactionService.update_transaction(payment.id, transaction.id, '123451',
                                                               skip_auth_check=True)

    assert transaction is not None
    assert transaction.id is not None
    assert transaction.status_code is not None
    assert transaction.payment_id is not None
    assert transaction.client_system_url is not None
    assert transaction.pay_system_url is not None
    assert transaction.transaction_start_time is not None
    assert transaction.transaction_end_time is not None
    assert transaction.status_code == Status.COMPLETED.value


@skip_in_pod
def test_transaction_update_with_no_receipt(session, stan_server):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id, invoice_number= '').save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    transaction = PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)
    transaction = PaymentTransactionService.update_transaction(payment.id, transaction.id, None, skip_auth_check=True)

    assert transaction is not None
    assert transaction.id is not None
    assert transaction.status_code is not None
    assert transaction.payment_id is not None
    assert transaction.client_system_url is not None
    assert transaction.pay_system_url is not None
    assert transaction.transaction_start_time is not None
    assert transaction.transaction_end_time is not None
    assert transaction.status_code == Status.FAILED.value
    assert transaction.asdict() is not None


@skip_in_pod
def test_transaction_update_completed(session, stan_server):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    transaction = PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)
    transaction = PaymentTransactionService.update_transaction(payment.id, transaction.id, '123451',
                                                               skip_auth_check=True)

    with pytest.raises(BusinessException) as excinfo:
        PaymentTransactionService.update_transaction(payment.id, transaction.id, '123451', skip_auth_check=True)
    assert excinfo.value.status == Error.PAY006.status
    assert excinfo.value.message == Error.PAY006.message
    assert excinfo.value.code == Error.PAY006.name


def test_transaction_create_new_on_completed_payment(session):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment(payment_status_code= Status.COMPLETED.value)
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    with pytest.raises(BusinessException) as excinfo:
        PaymentTransactionService.create(payment.id, {
            'clientSystemUrl': '',
            'payReturnUrl': ''
        }, skip_auth_check=True)
    assert excinfo.value.status == Error.PAY006.status
    assert excinfo.value.message == Error.PAY006.message
    assert excinfo.value.code == Error.PAY006.name


def test_multiple_transactions_for_single_payment(session):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)
    PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)
    transaction = PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)

    assert transaction is not None
    assert transaction.id is not None
    assert transaction.status_code is not None
    assert transaction.payment_id is not None
    assert transaction.client_system_url is not None
    assert transaction.pay_system_url is not None
    assert transaction.transaction_start_time is not None
    assert transaction.status_code == Status.CREATED.value


def test_transaction_invalid_lookup(session):
    """Invalid lookup.."""
    with pytest.raises(BusinessException) as excinfo:
        PaymentTransactionService.find_by_id(1, uuid.uuid4())
    assert excinfo.value.status == Error.PAY008.status
    assert excinfo.value.message == Error.PAY008.message
    assert excinfo.value.code == Error.PAY008.name


def test_transaction_invalid_update(session):
    """Invalid update.."""
    with pytest.raises(BusinessException) as excinfo:
        PaymentTransactionService.update_transaction(1, uuid.uuid4(), None, skip_auth_check=True)
    assert excinfo.value.status == Error.PAY008.status
    assert excinfo.value.message == Error.PAY008.message
    assert excinfo.value.code == Error.PAY008.name


def test_transaction_find_active_lookup(session):
    """Invalid lookup.."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()
    transaction = factory_payment_transaction(payment.id, Status.CREATED.value)
    transaction.save()

    transaction = PaymentTransactionService.find_active_by_payment_id(payment.id)
    assert transaction is not None
    assert transaction.id is not None
    assert transaction.status_code is not None
    assert transaction.payment_id is not None
    assert transaction.client_system_url is not None
    assert transaction.pay_system_url is not None
    assert transaction.transaction_start_time is not None
    assert transaction.status_code == Status.CREATED.value


def test_transaction_find_active_none_lookup(session):
    """Invalid lookup.."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()
    transaction = factory_payment_transaction(payment.id, Status.COMPLETED.value)
    transaction.save()

    transaction = PaymentTransactionService.find_active_by_payment_id(payment.id)
    assert transaction is None


def test_transaction_find_by_payment_id(session):
    """Find all transactions by payment id.."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()
    transaction = factory_payment_transaction(payment.id, Status.CREATED.value)
    transaction.save()

    transaction = PaymentTransactionService.find_by_payment_id(payment.id)
    assert transaction is not None
    assert transaction.get('items') is not None
    assert transaction.get('items')[0].get('_links') is not None


def test_no_existing_transaction(session):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    transaction = PaymentTransactionService.find_active_by_payment_id(payment.id)

    assert transaction is None


@skip_in_pod
def test_transaction_update_on_paybc_connection_error(session, stan_server):
    """Assert that the payment is saved to the table."""
    payment_account = factory_payment_account()
    payment = factory_payment()
    payment_account.save()
    payment.save()
    invoice = factory_invoice(payment.id, payment_account.id)
    invoice.save()
    factory_invoice_reference(invoice.id).save()
    fee_schedule = FeeSchedule.find_by_filing_type_and_corp_type('CP', 'OTANN')
    line = factory_payment_line_item(invoice.id, fee_schedule_id=fee_schedule.fee_schedule_id)
    line.save()

    transaction = PaymentTransactionService.create(payment.id, {
        'clientSystemUrl': '',
        'payReturnUrl': ''
    }, skip_auth_check=True)

    from unittest.mock import patch
    from requests.exceptions import ConnectTimeout, ConnectionError

    # Mock here that the invoice update fails here to test the rollback scenario
    with patch('pay_api.services.oauth_service.requests.post', side_effect=ConnectionError('mocked error')):
        transaction = PaymentTransactionService.update_transaction(payment.id, transaction.id, '123451',
                                                                   skip_auth_check=True)
        assert transaction.pay_system_reason_code == 'SERVICE_UNAVAILABLE'
    with patch('pay_api.services.oauth_service.requests.post', side_effect=ConnectTimeout('mocked error')):
        transaction = PaymentTransactionService.update_transaction(payment.id, transaction.id, '123451',
                                                                   skip_auth_check=True)
        assert transaction.pay_system_reason_code == 'SERVICE_UNAVAILABLE'

    assert transaction is not None
    assert transaction.id is not None
    assert transaction.status_code is not None
    assert transaction.payment_id is not None
    assert transaction.client_system_url is not None
    assert transaction.pay_system_url is not None
    assert transaction.transaction_start_time is not None
    assert transaction.transaction_end_time is not None
    assert transaction.status_code == Status.FAILED.value

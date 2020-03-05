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
"""Resource for BCOL accounts related operations."""

from http import HTTPStatus

from flask import current_app, request
from flask_restplus import Namespace, Resource

from bcol_api.exceptions import BusinessException
from bcol_api.schemas import utils as schema_utils
from bcol_api.services.bcol_payment import BcolPayment
from bcol_api.utils.auth import jwt as _jwt
from bcol_api.utils.trace import tracing as _tracing
from bcol_api.utils.util import cors_preflight


API = Namespace('bcol accounts', description='Payment System - BCOL Accounts')


@cors_preflight(['POST', 'OPTIONS'])
@API.route('', methods=['POST', 'OPTIONS'])
class AccountPayment(Resource):
    """Endpoint resource to manage BCOL Payments."""

    @staticmethod
    @_tracing.trace()
    @_jwt.requires_auth
    def post():
        """Create a payment record in BCOL."""
        try:
            req_json = request.get_json()
            current_app.logger.debug(req_json)
            # Validate the input request
            valid_format = schema_utils.validate(req_json, 'payment_request')
            if not valid_format[0]:
                current_app.logger.info('Validation Error with incoming request',
                                        schema_utils.serialize(valid_format[1]))
                response, status = {'code': 'BCOL999', 'message': 'Invalid Request'}, HTTPStatus.BAD_REQUEST
            else:
                response, status = BcolPayment().create_payment(req_json), HTTPStatus.OK
        except BusinessException as exception:
            response, status = {'code': exception.code, 'message': exception.message}, exception.status
        return response, status
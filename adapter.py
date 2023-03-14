import base64
import datetime
import json
import logging
import sys
import time
import traceback

from collections import namedtuple
from random import randrange

from kubernetes.client.rest import ApiException
from kubernetes import client, config

Usage = namedtuple('Usage', 'usage version timestamp')
namespace = 'neuvector-csp-billing-adapter'


def meter_billing(
    product_code: str,
    timestamp: int,
    dimension: str,
    quantity: int
):
    seed = randrange(10)

    if seed == 4:
        raise Exception('Unable to submit meter usage. Payment not billed!')
    else:
        return '1234567890'


def get_usage_data():
    api = client.CustomObjectsApi()
    resource = api.get_namespaced_custom_object(
        group="neuvector.com",
        version="v1",
        name="neuvector-usage",
        namespace="",
        plural="neuvectorusagerecords",
    )
    usage = Usage(
        resource.get('usage'),
        resource.get('version'),
        resource.get('timestamp')
    )
    return usage


def get_csp_config():
    api_instance = client.CoreV1Api()
    try:
        resp = api_instance.read_namespaced_config_map(
            'csp-config',
            namespace
        )
    except ApiException as error:
        if error.status == 404:
            return None
        else:
            raise
    else:
        return json.loads(resp.data.get('data', '{}'))



def update_csp_config(
    support_eligible: bool = None,
    csp: str = None,
    account_number: str = None,
    platform: str = None,
    product: str = None,
    message: str = None
):
    api_instance = client.CoreV1Api()
    data = get_csp_config()

    if support_eligible is not None:
        data['support_eligible'] = support_eligible

    if csp is not None:
        data['csp'] = csp

    if account_number is not None:
        data['account_number'] =account_number

    if platform is not None:
        data['platform'] = platform

    if product is not None:
        data['product'] = product

    if message is not None:
        data['message'] = message

    api_instance.patch_namespaced_config_map(
        'csp-config',
        namespace,
        data
    )


def create_csp_config():
    api_instance = client.CoreV1Api()
    data = {
        'data': json.dumps({
            'support_eligible': True,
            'csp': {
                'name': 'aws',
                'acct_number': '123451234567'
            },
            'platform': 'x86_64',
            'product': 'cpe:/o:suse:neuvector:v5.1.0',
            'usage': 0
        })
    }

    config_map = client.V1ConfigMap(
        data=data,
        metadata=client.V1ObjectMeta(
            name='csp-config',
            namespace=namespace
        )
    )

    api_instance.create_namespaced_config_map(
        namespace,
        config_map
    )


def get_now():
    return datetime.datetime.now(datetime.timezone.utc)


def date_to_string(date):
    return date.isoformat()


def string_to_date(timestamp):
    return datetime.datetime.fromisoformat(timestamp)


def create_cache():
    api_instance = client.CoreV1Api()
    data = {
        'maximum_usage': 0,
        'adapter_start_time': date_to_string(get_now()),
        'usage_records': [],
        'last_bill': {}
    }

    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(
            name='csp-adapter-cache',
            namespace=namespace
        ),
        string_data={'data': json.dumps(data)},
        type='Opaque'
    )
    api_instance.create_namespaced_secret(
        namespace,
        secret
    )


def get_cache():
    api_instance = client.CoreV1Api()
    try:
        resource = api_instance.read_namespaced_secret(
            'csp-adapter-cache',
            namespace,
        )
    except ApiException as error:
        if error.status == 404:
            return None
        else:
            raise
    else:
        return json.loads(base64.b64decode(resource.data.get('data')).decode())


def update_usage(current_usage: int):
    api_instance = client.CoreV1Api()
    cache = get_cache(api_instance)

    if current_usage > cache.get('max_usage', 0):
        api_instance.patch_namespaced_secret(
            'csp-adapter-cache',
            namespace,
            {'max_usage': current_usage},
        )


def cache_meter_record(
    record_id: str,
    quantity: int,
    dimension: str,
    timestamp: int
):
    api_instance = client.CoreV1Api()
    api_instance.patch_namespaced_secret(
        'csp-adapter-cache',
        namespace,
        {
            'last_bill': {
                'quantity': billed_usage,
                'dimension': dimension,
                'record_id': record_id,
                'timestamp': timestamp
            }
        }
    )


def main():
    config.load_kube_config()

    try:
        logging.basicConfig()
        log = logging.getLogger('CSPBillingAdapter')
        log.setLevel(logging.INFO)

        csp_config = get_csp_config()
        if not csp_config:
            create_csp_config()

        cache = get_cache()
        if not cache:
            create_cache()

        while True:
            usage = get_usage_data()
            update_usage(usage.usage)

            now = get_now()
            mins = now.strftime('%S')
            if mins.endswith('5'):
                max_usage = get_max_usage()

                try:
                    record_id = meter_billing(
                        product_code='123456789',
                        timestamp=now,
                        dimension='single',
                        quantity=max_usage
                    )
                except Exception as e:
                    update_csp_config(
                        support_eligible=False,
                        message=str(e),
                    )
                else:
                    cache_meter_record(
                        record_id=record_id,
                        quantity=max_usage,
                        dimension='single',
                        timestamp=date_to_string(now)
                    )

            time.sleep(60)
    except KeyboardInterrupt:
        sys.exit(0)
    except SystemExit as e:
        # user exception, program aborted by user
        sys.exit(e)
    except Exception as e:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error: {0}'.format(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

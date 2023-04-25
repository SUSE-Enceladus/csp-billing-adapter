import math

from csp_billing_adapter.csp_cache import cache_meter_record
from csp_billing_adapter.utils import (
    date_to_string,
    get_next_bill_time,
    get_now,
    get_date_delta,
    string_to_date
)
from csp_billing_adapter.config import Config


def get_max_usage(metric: str, usage_records: list):
    # In case of no records usage is 0
    # This prevents value error when calling max
    if not usage_records:
        return 0

    max_usage = max(record.get(metric, 0) for record in usage_records)
    return max_usage


def get_average_usage(metric: str, usage_records: list):
    # In case of no records usage is 0
    # This prevents divide by zero to get average
    if not usage_records:
        return 0

    total_usage = sum(record.get(metric, 0) for record in usage_records)
    average_usage = math.ceil(total_usage / len(usage_records))

    return average_usage


def get_billable_usage(
    usage_records: list,
    config: Config,
    empty_usage: False
):
    billable_usage = {}

    if empty_usage:
        return {metric: 0 for metric in config.usage_metrics}

    for metric, data in config.usage_metrics.items():
        if data['usage_aggregation'] == 'average':
            usage = get_average_usage(metric, usage_records)
        elif data['usage_aggregation'] == 'maximum':
            usage = get_max_usage(metric, usage_records)

        billable_usage[metric] = max(
            usage,
            data.get('minimum_consumption', 0)
        )

    return billable_usage


def get_volume_dimensions(
    usage_metric: str,
    usage: int,
    metric_dimensions: dict,
    billed_dimensions: dict
):
    for dimension in metric_dimensions:
        if 'min' in dimension and usage < dimension['min']:
            continue

        if 'max' in dimension and usage > dimension['max']:
            continue

        billed_dimensions[dimension['dimension']] = usage

        # All usage is billed in volume to the matching dimension
        break


def get_billing_dimensions(config: Config, billable_usage: dict):
    billed_dimensions = {}

    for usage_metric, usage in billable_usage.items():
        metric_config = config.usage_metrics[usage_metric]
        consumption_reporting = metric_config['consumption_reporting']

        if consumption_reporting == 'volume':
            get_volume_dimensions(
                usage_metric,
                usage,
                metric_config['dimensions'],
                billed_dimensions
            )
        else:
            # Stubbed for different consumption reporting models in future
            pass

    return billed_dimensions


def process_metering(
    config: Config,
    cache: dict,
    hook,
    empty_metering: bool = False
):
    now = get_now()

    billable_usage = get_billable_usage(
        cache.get('usage_records', []),
        config,
        empty_usage=empty_metering
    )
    billed_dimensions = get_billing_dimensions(
        config,
        billable_usage
    )

    try:
        record_id = hook.meter_billing(
            config=config,
            dimensions=billed_dimensions,
            timestamp=now
        )
    except Exception as e:
        hook.update_csp_config(
            config=config,
            csp_config={
                'billing_api_access_ok': False,
                'errors': [str(e)]
            },
            replace=False
        )
    else:
        metering_time = date_to_string(now)
        next_reporting_time = date_to_string(
            get_date_delta(now, config.reporting_interval)
        )

        data = {
            'billing_api_access_ok': True,
            'errors': [],
            'timestamp': metering_time,
            'expire': next_reporting_time
        }

        if not empty_metering:
            # Usage was billed
            next_bill_time = date_to_string(
                get_next_bill_time(
                    string_to_date(cache['next_bill_time']),
                    config.billing_interval
                )
            )

            cache_meter_record(
                hook,
                config,
                record_id,
                billed_dimensions,
                metering_time,
                next_bill_time
            )

            data['usage'] = billable_usage
            data['last_billed'] = metering_time

        hook.update_csp_config(
            config=config,
            csp_config=data,
            replace=False
        )
        hook.update_cache(
            config=config,
            cache={'next_reporting_time': next_reporting_time},
            replace=False
        )

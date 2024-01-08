The csp-billing-adapter requires a configuration file, (defaults to `/etc/csp_billing_adapter/config.yaml`)
in order to run successfully. The configuration files in the `examples` directory 
contain examples for the different product configurations. The default path can be overridden using the environment variable CSP_ADAPTER_CONFIG_FILE. For example:

`export CSP_ADAPTER_CONFIG_FILE=/tmp/my_config.yaml`

This README provides a listing of all of the fields and descriptions.
Fields that are optional are labeled accordingly.

```
version:
    The version of the configuration structure implementation.

billing_interval:
    Sets the billing interval time period.

api: (OPTIONAL)
    Provides the path to the application information the csp-billing-adapter reports to the CSP API.
    This is shared with the application the csp-billng-adapter is reporting about. The application may provide this as an endpoint directly, i.e. http://localhost/$API works.

product_code:
    TBD

query_interval:
    Time in seconds for how often the csp-billng-adapter collects the data from the application.

reporting_api_is_cumulative:
    Specifies if the CSP will accumulate reported values. While all CSPs will accumulate the values reported, it may not be possible to report 0. For example, in a monthly billing scenario, the csp-billing-adapter may have to report on a hourly basis a number that is not 0 such that the CSP API accumulates the values. A true setting would direct the adapater to normalize the unit count based on some to be determined normalization algorithm.

reporting_interval: 
    Sets the time in seconds when the csp-billing-adapter reports to the CSP API. The values the csp-billing-adapter reports are determined by a combination of the settings for `reporting_api_is_cumulative` and `billing_interval`.

archive_retention_period:
    Sets the time in months that metering data is retained in the data archive.

usage_metrics: 

  {metric name}:
    The name of the metric, for example managed_node_count

    consumption_reporting:
        Sets the way the csp-billing-adapter reports the value(s) it receives, either `volume` or `tiered`.

        The `volume` value triggers the code to search for the highest possible dimension to use and all other configured dimensions will be reported as 0, or not reported, depending on CSP API requirements. For example:
        
            - The configuration is set to volume for the consumption_reporting
            - The dimensions configuration contains 3 dimensions with a maximum setting of 30, 40, and 55
            
            If the value reported by the application API is 150:
            
                The csp-billing-adapter will report 0 for dimension 1 and 2 and report 150 for dimension 3.
            
            If the application API reports 36:

                The csp-billing-adapter will report 0 for dimension 1, 36 for dimension 2, and 0 for dimension 3.
            
            In this case the application API may report only 1 dimension. 
            
            If consumption_reporting is set to volume and the application API ad the application API reports more than 1 dimension it is an error condition.

        The `tiered` value triggers the code to report per dimension. This has 2 implied reporting mechanisms.

            One use case is the application API reports dimensions that match the configuration.

                In this case, the csp-billing-adapter reports the count per dimension as reported by the application API.

            The second use case is for the application API to return only 1 value

                In this case the code will divide the reported value into categories reporting for each dimension the maximum value possible. For example:
                
                - There are 3 dimensions with a maximum setting of 30, 40, and 55
                - A minimum setting of 0, 31, and 41
                
                The application reports a unit count of 150:
                
                    The csp-billing-adapter will report 30 units for dimension 1, 10 units for dimension 2, and 110 units for dimension 3.
                   
                The application API reports 36:

                    The csp-billing-adapter will report 30 units for dimension 1 and 6 units for dimension 2, and 0 units for dimension 3.

    usage_aggregation:
        The value the csp-billing-adapter reports. The maximum over the reporting time period, the current value, or the average over the reporting time period:

            maximum
                When set to this value, the billing adapter queries the application API hourly and stores the retrieved information in the internal data structure. The csp-billing-adapter stores the maximum value. When the billing adapter reports to the CSP API, the csp-billing-adapter retrieves this value and this is the reported number of units. The internal counter is reset to 0.

            current
                (NOT IMPLEMENTED) When set to this value, the billing adapter does not need to store any data from the application, it can query the application API and then directly report the value to the CSP API.

            average
                When set to this value, the billing adapter queries the application API hourly and stores the retrieved information in the internal data structure. When the billing adapter reports to the CSP API the average over all values is calculated and this is the number of units being reported. This calculation is rounded up to the nearest integer unit. The internal storage structure is cleared. Expressed differently sum_of_all_numbers_in_array / length_of_array
    
    min_consumption: (OPTIONAL)
        count 
            Set the minimum unit count the csp-billing-adapter will report. If the application reports a total unit count greater than 0 and less than this number this is the value the csp-billing-adapter will use instead of the application reported number.
    
    dimensions:
        The dimensions correspond to the setup in the CSP listing, the AWS load form, the Azure offer, or the GCP pricing-model. 


    - dimension: {dimension id}

      min: (OPTIONAL) [inclusive] 
        This is the minimum number of units to report for this dimension. The adapter reports for a dimension if the unit count is in the range of min and max per the consumption_reporting setting. See max below for more detail.

      max: (OPTIONAL) [inclusive] 
        This is the maximum number of units to report in this dimension. This is a soft limit.
          If the application API reports a number greater than the maximum of a dimension, the csp-billing-adapter will look for another dimension where the reported unit count is greater than the configured min

          If the consumption_reporting is set to tiered, the csp-billing-adapter will report application_units - maximum for each dimension where total number of units is greater than max.  If there are no more dimensions, the csp-billing-adapter will report any remainder as units of the last dimension specified.

          If the consumption_reporting is set to volume, the csp-billing-adapter will report all units in the dimension where the total number of units is greater than min and less than max, if max is configured.
```

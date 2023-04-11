import pluggy

__author__ = """SUSE"""
__email__ = 'public-cloud-dev@susecloud.net'
__version__ = '0.0.1'

hookimpl = pluggy.HookimplMarker('csp_billing_adapter')
"""Marker to be imported and used in plugins (and for own implementations)"""

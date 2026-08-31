class ProviderError(RuntimeError):
    status = "provider_error"


class ProviderConfigurationError(ProviderError):
    status = "configuration_error"


class ProviderValidationError(ProviderError):
    status = "validation_error"


class ProviderRateLimitedError(ProviderError):
    status = "rate_limited"


class ProviderSchemaDriftError(ProviderError):
    status = "schema_drift"

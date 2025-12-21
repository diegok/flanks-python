from flanks import (
    FlanksAPIError,
    FlanksAuthError,
    FlanksConfigError,
    FlanksError,
    FlanksNetworkError,
    FlanksNotFoundError,
    FlanksServerError,
    FlanksValidationError,
)


class TestExceptionHierarchy:
    def test_flanks_error_is_base(self) -> None:
        error = FlanksError("test")
        assert isinstance(error, Exception)
        assert str(error) == "test"

    def test_config_error_inherits_from_flanks_error(self) -> None:
        error = FlanksConfigError("missing credentials")
        assert isinstance(error, FlanksError)

    def test_api_error_has_status_and_body(self) -> None:
        error = FlanksAPIError(
            "bad request",
            status_code=400,
            response_body={"error": "validation failed"},
        )
        assert isinstance(error, FlanksError)
        assert error.status_code == 400
        assert error.response_body == {"error": "validation failed"}
        assert str(error) == "bad request"

    def test_api_error_optional_fields(self) -> None:
        error = FlanksAPIError("error")
        assert error.status_code is None
        assert error.response_body is None

    def test_auth_error_inherits_from_api_error(self) -> None:
        error = FlanksAuthError("unauthorized", status_code=401)
        assert isinstance(error, FlanksAPIError)
        assert isinstance(error, FlanksError)

    def test_validation_error_inherits_from_api_error(self) -> None:
        error = FlanksValidationError("invalid", status_code=400)
        assert isinstance(error, FlanksAPIError)

    def test_not_found_error_inherits_from_api_error(self) -> None:
        error = FlanksNotFoundError("not found", status_code=404)
        assert isinstance(error, FlanksAPIError)

    def test_server_error_inherits_from_api_error(self) -> None:
        error = FlanksServerError("server error", status_code=500)
        assert isinstance(error, FlanksAPIError)

    def test_network_error_has_cause(self) -> None:
        cause = ConnectionError("connection refused")
        error = FlanksNetworkError("network failure", cause=cause)
        assert isinstance(error, FlanksError)
        assert not isinstance(error, FlanksAPIError)
        assert error.__cause__ is cause

    def test_network_error_optional_cause(self) -> None:
        error = FlanksNetworkError("timeout")
        assert error.__cause__ is None

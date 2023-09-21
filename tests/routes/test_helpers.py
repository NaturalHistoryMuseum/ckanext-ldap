from unittest.mock import patch, MagicMock

import pytest

from ckan.lib.helpers import url_for
from ckanext.ldap.routes._helpers import login_failed


@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SADeprecationWarning")
@pytest.mark.usefixtures("with_request_context")
@patch("ckan.plugins.toolkit.h.flash_error")
@patch("ckan.plugins.toolkit.h.flash_notice")
def test_login_failed(flash_notice_mock: MagicMock, flash_error_mock: MagicMock):
    notice = "A notice!"
    error = "An error!"
    response = login_failed(notice=notice, error=error)

    flash_notice_mock.assert_called_once_with(notice)
    flash_error_mock.assert_called_once_with(error)
    assert response.status_code == 302
    assert response.location.endswith(url_for("user.login"))

from unittest.mock import patch, MagicMock

import pytest

from ckan.lib.helpers import url_for
from ckanext.ldap.routes._helpers import login_failed, login_success


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


@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SADeprecationWarning")
@pytest.mark.usefixtures("with_request_context")
def test_login_success():
    username = "a_user"
    came_from = "somewhere_else"

    with patch("ckanext.ldap.routes._helpers.session") as mock_session:
        response = login_success(username, came_from)

    mock_session.__setitem__.assert_called_once_with("ckanext-ldap-user", username)
    assert mock_session.save.called
    assert response.status_code == 302
    assert response.location.endswith(
        f'{url_for("user.logged_in")}?came_from={came_from}'
    )

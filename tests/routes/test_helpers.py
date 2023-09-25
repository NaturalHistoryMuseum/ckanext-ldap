from unittest.mock import patch, MagicMock

import pytest

from ckan.lib.helpers import url_for
from ckan.plugins import toolkit
from ckan.tests import factories
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


IS_CKAN_210_OR_HIGHER = toolkit.check_ckan_version(min_version="2.10.0")
IS_CKAN_29_OR_LOWER = not IS_CKAN_210_OR_HIGHER


@pytest.mark.skipif(IS_CKAN_210_OR_HIGHER, reason="requires CKAN 2.9 or lower")
@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SADeprecationWarning")
class TestLoginSuccess29:
    # these tests are only run on CKAN 2.9

    @pytest.mark.usefixtures("with_request_context")
    @patch("ckanext.ldap.routes._helpers.session")
    @patch("ckan.plugins.toolkit.h.flash_error")
    def test_ok(self, flash_error_mock: MagicMock, mock_session: MagicMock):
        username = "some_username"
        came_from = "somewhere_else"

        response = login_success(username, came_from)

        # check no errors
        flash_error_mock.assert_not_called()
        # check the username was put in the session
        mock_session.__setitem__.assert_called_once_with("ckanext-ldap-user", username)

        assert mock_session.save.called
        assert response.status_code == 302

        assert response.location.endswith(
            f"{url_for('user.logged_in')}?came_from={came_from}"
        )


@pytest.mark.skipif(IS_CKAN_29_OR_LOWER, reason="requires CKAN 2.10 or higher")
@pytest.mark.filterwarnings("ignore::sqlalchemy.exc.SADeprecationWarning")
class TestLoginSuccess210:
    # these tests are only run on CKAN 2.10
    @pytest.mark.usefixtures("with_request_context")
    @patch("ckan.plugins.toolkit.login_user", return_value=True)
    @patch("ckanext.ldap.routes._helpers.session")
    @patch("ckan.plugins.toolkit.h.flash_error")
    def test_ok(
        self,
        flash_error_mock: MagicMock,
        mock_session: MagicMock,
        login_user: MagicMock,
    ):
        user = factories.User()
        username = user["name"]
        came_from = "somewhere_else"

        response = login_success(username, came_from)

        # check no errors
        flash_error_mock.assert_not_called()
        # check the username was put in the session
        mock_session.__setitem__.assert_called_once_with("ckanext-ldap-user", username)

        assert mock_session.save.called
        assert response.status_code == 302

        assert login_user.called

        assert response.location.endswith(
            f"{url_for('home.index')}?came_from={came_from}"
        )

    @pytest.mark.usefixtures("with_request_context")
    @patch("ckan.plugins.toolkit.login_user", return_value=True)
    @patch("ckanext.ldap.routes._helpers.session")
    @patch("ckan.plugins.toolkit.h.flash_error")
    @patch("ckan.model.User.by_name", side_effect=toolkit.ObjectNotFound())
    def test_user_not_found(
        self,
        mock_by_name: MagicMock,
        flash_error_mock: MagicMock,
        mock_session: MagicMock,
        login_user: MagicMock,
    ):
        username = "not_in_the_db"
        came_from = "somewhere_else"

        response = login_success(username, came_from)

        # check an error was flashed
        flash_error_mock.assert_called_once()
        # check the username was not put in the session
        assert not mock_session.__setitem__.called
        assert not mock_session.save.called
        assert not login_user.called
        assert response.status_code == 302
        assert response.location.endswith(url_for("user.login"))

    @pytest.mark.usefixtures("with_request_context")
    @patch("ckan.plugins.toolkit.login_user", return_value=True)
    @patch("ckanext.ldap.routes._helpers.session")
    @patch("ckan.plugins.toolkit.h.flash_error")
    @patch("ckan.model.User.by_name", return_value=None)
    def test_user_object_is_none(
        self,
        mock_by_name: MagicMock,
        flash_error_mock: MagicMock,
        mock_session: MagicMock,
        login_user: MagicMock,
    ):
        username = "not_in_the_db"
        came_from = "somewhere_else"

        response = login_success(username, came_from)

        # check an error was flashed
        flash_error_mock.assert_called_once()
        # check the username was not put in the session
        assert not mock_session.__setitem__.called
        assert not mock_session.save.called
        assert not login_user.called
        assert response.status_code == 302
        assert response.location.endswith(url_for("user.login"))

    @pytest.mark.usefixtures("with_request_context")
    @patch("ckan.plugins.toolkit.login_user", return_value=False)
    @patch("ckanext.ldap.routes._helpers.session")
    @patch("ckan.plugins.toolkit.h.flash_error")
    def test_login_user_not_ok(
        self,
        flash_error_mock: MagicMock,
        mock_session: MagicMock,
        login_user: MagicMock,
    ):
        username = "not_in_the_db"
        came_from = "somewhere_else"

        response = login_success(username, came_from)

        # check an error was flashed
        flash_error_mock.assert_called_once()
        # check the username was not put in the session
        assert not mock_session.__setitem__.called
        assert not mock_session.save.called
        assert not login_user.called
        assert response.status_code == 302
        assert response.location.endswith(url_for("user.login"))

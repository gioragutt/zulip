# -*- coding: utf-8 -*-

from zerver.lib.actions import get_realm, do_add_realm_filter
from zerver.lib.test_classes import ZulipTestCase
from zerver.models import RealmFilter

class RealmFilterTest(ZulipTestCase):
    BLANK_FIELD_ERROR = 'This field cannot be blank.'
    INVALID_PATTERN_ERROR = 'Invalid filter pattern, you must use the following format OPTIONAL_PREFIX(?P<id>.+)'
    INVALID_URL_ERROR = 'Enter a valid URL.'
    INVALID_URL_FORMAT_ERROR = 'URL format string must be in the following format: `https://example.com/%(\\w+)s`'

    def test_list(self) -> None:
        email = self.example_email('iago')
        self.login(email)
        realm = get_realm('zulip')
        do_add_realm_filter(
            realm,
            "#(?P<id>[123])",
            "https://realm.com/my_realm_filter/%(id)s")
        result = self.client_get("/json/realm/filters")
        self.assert_json_success(result)
        self.assertEqual(200, result.status_code)
        self.assertEqual(len(result.json()["filters"]), 1)

    def assert_filter_not_created(self, pattern: str, url_format_string: str, error: str) -> None:
        data = {"pattern": pattern, "url_format_string": url_format_string}
        result = self.client_post("/json/realm/filters", info=data)
        self.assert_json_error(result, error)

    def assert_filter_created(self, pattern: str, url_format_string: str) -> None:
        data = {"pattern": pattern, "url_format_string": url_format_string}
        result = self.client_post("/json/realm/filters", info=data)
        self.assert_json_success(result)

    def test_create(self) -> None:
        email = self.example_email('iago')
        self.login(email)

        self.assert_filter_not_created(pattern="",
                                       url_format_string="https://realm.com/my_realm_filter/%(id)s",
                                       error=self.BLANK_FIELD_ERROR)

        self.assert_filter_not_created(pattern="$a",
                                       url_format_string="https://realm.com/my_realm_filter/%(id)s",
                                       error=self.INVALID_PATTERN_ERROR)

        self.assert_filter_not_created(pattern='ZUL-(?P<id>\d++)',
                                       url_format_string="https://realm.com/my_realm_filter/%(id)s",
                                       error=self.INVALID_PATTERN_ERROR)

        self.assert_filter_not_created(pattern='ZUL-(?P<id>\d+)',
                                       url_format_string='$fgfg',
                                       error=self.INVALID_URL_ERROR)

        self.assert_filter_not_created(pattern='ZUL-(?P<id>\d+)',
                                       url_format_string='https://realm.com/my_realm_filter/',
                                       error=self.INVALID_URL_FORMAT_ERROR)

        self.assert_filter_created(pattern='ZUL-(?P<id>\d+)',
                                   url_format_string='https://realm.com/my_realm_filter/%(id)s')

        self.assert_filter_created(pattern='ZUL2-(?P<id>\d+)',
                                   url_format_string='https://realm.com/my_realm_filter/?value=%(id)s')

        self.assert_filter_created(pattern='ZUL3-(?P<id>\d+)',
                                   url_format_string='https://realm.com/#/my_realm_filter/?value=%(id)s')

    def test_not_realm_admin(self) -> None:
        email = self.example_email('hamlet')
        self.login(email)
        result = self.client_post("/json/realm/filters")
        self.assert_json_error(result, 'Must be an organization administrator')
        result = self.client_delete("/json/realm/filters/15")
        self.assert_json_error(result, 'Must be an organization administrator')

    def test_delete(self) -> None:
        email = self.example_email('iago')
        self.login(email)
        realm = get_realm('zulip')
        filter_id = do_add_realm_filter(
            realm,
            "#(?P<id>[123])",
            "https://realm.com/my_realm_filter/%(id)s")
        filters_count = RealmFilter.objects.count()
        result = self.client_delete("/json/realm/filters/{0}".format(filter_id + 1))
        self.assert_json_error(result, 'Filter not found')

        result = self.client_delete("/json/realm/filters/{0}".format(filter_id))
        self.assert_json_success(result)
        self.assertEqual(RealmFilter.objects.count(), filters_count - 1)

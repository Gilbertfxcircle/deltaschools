"""LAW #1: Tenant isolation.

These tests prove the schema-resolution layer cannot be tricked into producing
an unsafe schema name, and that distinct tenants always resolve to distinct
schemas. The runtime guarantee (School A cannot read School B) is built on
``schema_for_tenant`` + ``search_path_sql``; a live cross-tenant read test
against PostgreSQL lives in the integration suite (requires a running DB).
"""

import unittest

from app.core.tenant import (
    GLOBAL_SCHEMA,
    TenantError,
    is_safe_schema_name,
    normalize_tenant_id,
    schema_for_tenant,
    search_path_sql,
    tenant_from_host,
)


class TestTenantResolution(unittest.TestCase):
    def test_distinct_tenants_map_to_distinct_schemas(self):
        self.assertEqual(schema_for_tenant("001"), "school_001")
        self.assertEqual(schema_for_tenant("stmarys"), "school_stmarys")
        self.assertNotEqual(schema_for_tenant("a"), schema_for_tenant("b"))

    def test_hyphens_become_underscores(self):
        self.assertEqual(schema_for_tenant("green-hill"), "school_green_hill")

    def test_case_is_normalized(self):
        self.assertEqual(schema_for_tenant("StMarys"), "school_stmarys")

    def test_reserved_subdomains_are_rejected(self):
        for reserved in ("admin", "api", "www", "deltaplax"):
            with self.assertRaises(TenantError):
                normalize_tenant_id(reserved)

    def test_missing_tenant_raises(self):
        with self.assertRaises(TenantError):
            normalize_tenant_id(None)
        with self.assertRaises(TenantError):
            normalize_tenant_id("")


class TestSchemaInjectionDefense(unittest.TestCase):
    """A malicious tenant id must never yield SQL-injectable schema names."""

    MALICIOUS = [
        'x"; DROP SCHEMA deltaplax_global; --',
        "abc; DELETE FROM students",
        "../../etc/passwd",
        "school_001; --",
        "a b",
        "tab\tname",
        "naughty'name",
    ]

    def test_malicious_tenant_ids_rejected(self):
        for bad in self.MALICIOUS:
            with self.assertRaises(TenantError):
                schema_for_tenant(bad)

    def test_search_path_sql_refuses_unsafe_names(self):
        with self.assertRaises(TenantError):
            search_path_sql('school_x"; DROP TABLE y')

    def test_search_path_sql_for_valid_schema(self):
        sql = search_path_sql(schema_for_tenant("001"))
        self.assertEqual(sql, f'SET search_path TO "school_001", "{GLOBAL_SCHEMA}"')

    def test_is_safe_schema_name(self):
        self.assertTrue(is_safe_schema_name("school_001"))
        self.assertTrue(is_safe_schema_name(GLOBAL_SCHEMA))
        self.assertFalse(is_safe_schema_name('school_001"'))
        self.assertFalse(is_safe_schema_name("school 001"))
        self.assertFalse(is_safe_schema_name("1school"))  # cannot start with digit


class TestHostExtraction(unittest.TestCase):
    def test_tenant_from_subdomain(self):
        self.assertEqual(tenant_from_host("stmarys.deltaplax.com", "deltaplax.com"), "stmarys")

    def test_apex_and_reserved_have_no_tenant(self):
        self.assertIsNone(tenant_from_host("deltaplax.com", "deltaplax.com"))
        self.assertIsNone(tenant_from_host("admin.deltaplax.com", "deltaplax.com"))

    def test_port_is_stripped(self):
        self.assertEqual(tenant_from_host("demo.deltaplax.com:8000", "deltaplax.com"), "demo")

    def test_foreign_domain_has_no_tenant(self):
        self.assertIsNone(tenant_from_host("evil.com", "deltaplax.com"))


if __name__ == "__main__":
    unittest.main()

from app.core.permissions import Capability, has_capability


class TestPermissions:
    def test_admin_can_manage_users(self):
        assert has_capability("admin", Capability.USER_MANAGE)

    def test_staff_cannot_manage_users(self):
        assert not has_capability("staff", Capability.USER_MANAGE)

    def test_admin_reads_all_altas(self):
        assert has_capability("admin", Capability.ALTA_READ_ALL)
        assert not has_capability("admin", Capability.ALTA_READ_OWN_SEDE)

    def test_staff_reads_own_sede_only(self):
        assert has_capability("staff", Capability.ALTA_READ_OWN_SEDE)
        assert not has_capability("staff", Capability.ALTA_READ_ALL)

    def test_only_admin_marks_sent(self):
        assert has_capability("admin", Capability.ALTA_MARK_SENT)
        assert not has_capability("staff", Capability.ALTA_MARK_SENT)

    def test_unknown_role_has_no_caps(self):
        assert not has_capability("ghost", Capability.ALTA_CREATE)
        assert not has_capability("", Capability.USER_MANAGE)

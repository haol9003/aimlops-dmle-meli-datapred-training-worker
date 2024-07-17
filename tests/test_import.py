"""A test module to check that version is compliant to PEP 396."""


def test_import_package():
    from dmle_meli_datapred_training_worker import __version__ as version

    assert version is not None
    assert isinstance(version, str)

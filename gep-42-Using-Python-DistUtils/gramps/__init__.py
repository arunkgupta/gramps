VERSION = (3, 5, 0, 'Final', 0)

def get_version(version =None):
    """Derives a PEP386-compliant version number from VERSION."""
    if version is None:
        version = VERSION
    assert len(version) == 5
    assert version[3] in ('Alpha', 'Beta', 'rc', 'Final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for Alpha, Beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] == 'Alpha' and version[4] == 0:
        # At the toplevel, this would cause an import loop.
        from gramps.const import VERSION as GRAMPS_VERSION
        sub = GRAMPS_VERSION[4:]

    elif version[3] != 'Final':
        mapping = {'Alpha': 'alpha', 'Beta': 'beta', 'rc': 'RC'}
        sub = mapping[version[3]] + str(version[4])
    return main + sub

from __future__ import annotations

import datetime
import decimal
import fractions
import pathlib
import re
import typing
import uuid

import pytest
from typelib import compat, refs
from typelib.unmarshal import api

from tests import models


@pytest.mark.suite(
    forwardref=dict(
        given_type=refs.forwardref("decimal.Decimal"),
        given_input="1.0",
        expected_output=decimal.Decimal("1.0"),
    ),
    unresolvable=dict(
        given_type=...,
        given_input="foo",
        expected_output="foo",
    ),
    nonetype=dict(
        given_type=None,
        given_input=None,
        expected_output=None,
    ),
    literal=dict(
        given_type=typing.Literal[1, 2, 3],
        given_input="2",
        expected_output=2,
    ),
    union=dict(
        given_type=typing.Union[int, str],
        given_input="2",
        expected_output=2,
    ),
    datetime=dict(
        given_type=datetime.datetime,
        given_input=0,
        expected_output=datetime.datetime.fromtimestamp(0, datetime.timezone.utc),
    ),
    date=dict(
        given_type=datetime.date,
        given_input=0,
        expected_output=datetime.datetime.fromtimestamp(
            0, datetime.timezone.utc
        ).date(),
    ),
    time=dict(
        given_type=datetime.time,
        given_input=0,
        expected_output=datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
        .time()
        .replace(tzinfo=datetime.timezone.utc),
    ),
    timedelta=dict(
        given_type=datetime.timedelta,
        given_input=0,
        expected_output=datetime.timedelta(seconds=0),
    ),
    uuid=dict(
        given_type=uuid.UUID,
        given_input=0,
        expected_output=uuid.UUID(int=0),
    ),
    pattern=dict(
        given_type=re.Pattern,
        given_input="1",
        expected_output=re.compile("1"),
    ),
    path=dict(
        given_type=pathlib.Path,
        given_input="/path/to/file",
        expected_output=pathlib.Path("/path/to/file"),
    ),
    decimal=dict(
        given_type=decimal.Decimal,
        given_input="1.0",
        expected_output=decimal.Decimal("1.0"),
    ),
    fraction=dict(
        given_type=fractions.Fraction,
        given_input="1/2",
        expected_output=fractions.Fraction("1/2"),
    ),
    string=dict(
        given_type=str,
        given_input=1,
        expected_output="1",
    ),
    bytes=dict(
        given_type=bytes,
        given_input=1,
        expected_output=b"1",
    ),
    bytearray=dict(
        given_type=bytearray,
        given_input=1,
        expected_output=bytearray(b"1"),
    ),
    memoryview=dict(
        given_type=memoryview,
        given_input="foo",
        expected_output=memoryview(b"foo"),
    ),
    typeddict=dict(
        given_type=models.TDict,
        given_input={"field": 1, "value": "2"},
        expected_output=models.TDict(field="1", value=2),
    ),
    direct_recursive=dict(
        given_type=models.RecursiveType,
        given_input={"cycle": {"cycle": {}}},
        expected_output=models.RecursiveType(
            cycle=models.RecursiveType(cycle=models.RecursiveType())
        ),
    ),
    indirect_recursive=dict(
        given_type=models.IndirectCycleType,
        given_input={"indirect": {"cycle": {"indirect": {}}}},
        expected_output=models.IndirectCycleType(
            indirect=models.CycleType(
                cycle=models.IndirectCycleType(indirect=models.CycleType())
            )
        ),
    ),
    type_alias_type=dict(
        given_type=compat.TypeAliasType("IntList", "list[int]"),
        given_input='["1", "2"]',
        expected_output=[1, 2],
    ),
)
def test_unmarshal(given_type, given_input, expected_output):
    # When
    output = api.unmarshal(given_type, given_input)
    # Then
    assert output == expected_output

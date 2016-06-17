import pytest

import gevent.monkey
import gevent

from rill.engine.runner import ComponentRunner
from rill.runtime import Runtime

from tests.components import *

import logging
ComponentRunner.logger.setLevel(logging.DEBUG)


# we use socket as our canary
is_patched = gevent.monkey.is_module_patched("socket")
requires_patch = pytest.mark.skipif(not is_patched,
                                    reason='requires patched gevent')

def test_get_graph_messages():
    """
    Test that runtime can build graph with graph protocol messages
    """
    graph_id = 'graph1'
    graph_name = 'My Graph'
    runtime = Runtime()
    runtime.new_graph(graph_id)

    net = runtime._get_graph(graph_id)
    net.name = graph_name

    gen = net.add_component('Generate', GenerateTestData)
    gen.metadata['x'] = 5
    gen.metadata['y'] = 5

    passthru = net.add_component('Pass', Passthru)
    outside = net.add_component('Outside', Passthru)

    net.connect('Generate.OUT', 'Pass.IN')
    net.connect('Outside.OUT', 'Pass.IN')
    net.initialize(5, 'Generate.COUNT')
    net.export('Pass.OUT', 'OUTPORT')
    net.export('Outside.IN', 'INPORT')

    messages = runtime.get_graph_messages(graph_id)
    assert ('clear', {
        'id': graph_id,
        'name': graph_name
    }) in messages

    assert ('addnode', {
        'graph': graph_id,
        'id': gen.get_name(),
        'component': gen.get_type(),
        'metadata': gen.metadata
    }) in messages
    assert ('addnode', {
        'graph': graph_id,
        'id': passthru.get_name(),
        'component': passthru.get_type(),
        'metadata': passthru.metadata
    }) in messages
    assert ('addnode', {
        'graph': graph_id,
        'id': outside.get_name(),
        'component': outside.get_type(),
        'metadata': outside.metadata
    }) in messages

    assert ('addedge', {
        'graph': graph_id,
        'src': {
            'node': gen.get_name(),
            'port': 'OUT'
        },
        'tgt': {
            'node': passthru.get_name(),
            'port': 'IN'
        }
    }) in messages
    assert ('addedge', {
        'graph': graph_id,
        'src': {
            'node': outside.get_name(),
            'port': 'OUT'
        },
        'tgt': {
            'node': passthru.get_name(),
            'port': 'IN'
        }
    }) in messages

    assert ('addinitial', {
        'graph': graph_id,
        'data': 5,
        'tgt': {
            'node': gen.get_name(),
            'port': 'COUNT'
        }
    }) in messages

    assert ('addinport', {
        'graph': graph_id,
        'public': 'INPORT',
        'node': outside.get_name(),
        'port': 'IN'
    }) in messages
    assert ('addoutport', {
        'graph': graph_id,
        'public': 'OUTPORT',
        'node': passthru.get_name(),
        'port': 'OUT'
    }) in messages



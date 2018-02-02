# -*- coding:utf-8 -*-

import sys
import time
import logging
import json

import pytest
import tornado
from tornado.httpclient import HTTPRequest, HTTPError
from tornado.testing import AsyncHTTPTestCase, gen_test


@pytest.fixture(scope="session")
def tf_logs(tmpdir_factory):

    import numpy as np
    import tensorflow as tf
    x = np.random.rand(5)
    y = 3 * x + 1 + 0.05 * np.random.rand(5)

    a = tf.Variable(0.1)
    b = tf.Variable(0.)
    err = a*x+b-y

    loss = tf.norm(err)
    tf.summary.scalar("loss", loss)
    tf.summary.scalar("a", a)
    tf.summary.scalar("b", b)
    merged = tf.summary.merge_all()

    optimizor = tf.train.GradientDescentOptimizer(0.01).minimize(loss)

    with tf.Session() as sess:
        log_dir = tmpdir_factory.mktemp("logs", numbered=False)
        log_dir = str(log_dir)

        train_write = tf.summary.FileWriter(log_dir, sess.graph)
        tf.global_variables_initializer().run()
        for i in range(1000):
            _, merged_ = sess.run([optimizor, merged])
            train_write.add_summary(merged_, i)

    return log_dir


@pytest.fixture(scope="session")
def nb_app():
    sys.argv = ["--port=6005", "--ip=127.0.0.1", "--no-browser", "--debug"]
    from notebook.notebookapp import NotebookApp
    app = NotebookApp()
    app.log_level = logging.DEBUG
    app.ip = '127.0.0.1'
    app.token = ''
    app.password = ''
    app.disable_check_xsrf = True
    app.initialize()
    return app.web_app


class TestJupyterExtension(AsyncHTTPTestCase):

    @pytest.fixture(autouse=True)
    def init_jupyter(self, tf_logs, nb_app, tmpdir_factory):
        self.app = nb_app
        self.log_dir = tf_logs
        self.tmpdir_factory = tmpdir_factory

    def get_app(self):
        return self.app

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    @gen_test
    def test_tensorboard(self):

        content = {"logdir": self.log_dir}
        content_type = {"Content-Type": "application/json"}
        request = HTTPRequest(
            url=self.get_url('/api/tensorboard'),
            method='POST',
            body=json.dumps(content),
            headers=content_type)
        response = yield self.http_client.fetch(request)

        request = HTTPRequest(url=self.get_url('/api/tensorboard'))
        response = yield self.http_client.fetch(request)
        instances = json.loads(response.body.decode())
        assert len(instances) > 0

        request = HTTPRequest(url=self.get_url('/api/tensorboard/1'))
        response = yield self.http_client.fetch(request)
        instance = json.loads(response.body.decode())
        instance2 = None
        for inst in instances:
            if inst["name"] == instance["name"]:
                instance2 = inst
        assert instance == instance2

        request = HTTPRequest(url=self.get_url('/tensorboard/1/#graphs'))
        response = yield self.http_client.fetch(request)
        assert response.code == 200

        request = HTTPRequest(
            url=self.get_url('/tensorboard/1/data/plugins_listing'))
        response = yield self.http_client.fetch(request)
        plugins_list = json.loads(response.body.decode())
        assert plugins_list["graphs"]
        assert plugins_list["scalars"]

        request = HTTPRequest(
            url=self.get_url('/api/tensorboard/1'),
            method='DELETE')
        response = yield self.http_client.fetch(request)
        assert response.code == 204

        request = HTTPRequest(url=self.get_url('/api/tensorboard/1'))
        with pytest.raises(HTTPError) as e:
            response = yield self.http_client.fetch(request)
            assert e.value.code == 404

    @gen_test(timeout=10)
    def test_instance_reload(self):
        content = {"logdir": self.log_dir, "reload_interval": 4}
        content_type = {"Content-Type": "application/json"}
        request = HTTPRequest(
            url=self.get_url('/api/tensorboard'),
            method='POST',
            body=json.dumps(content),
            headers=content_type)
        response = yield self.http_client.fetch(request)
        instance = json.loads(response.body.decode())
        assert instance is not None
        name = instance["name"]
        reload_time = instance["reload_time"]

        time.sleep(5)
        request = HTTPRequest(
            url=self.get_url('/api/tensorboard/{}'.format(name)))
        response = yield self.http_client.fetch(request)
        instance2 = json.loads(response.body.decode())
        assert instance2["reload_time"] != reload_time

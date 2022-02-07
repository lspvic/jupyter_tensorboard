# -*- coding:utf-8 -*-

import os
import sys
import time
import logging
import json
import binascii

import pytest
from tornado.testing import AsyncHTTPTestCase

def encode_multipart_formdata(fields):
    boundary = binascii.hexlify(os.urandom(16)).decode('ascii')

    body = (
        "".join("--%s\r\n"
                "Content-Disposition: form-data; name=\"%s\"\r\n"
                "\r\n"
                "%s\r\n" % (boundary, field, value)
                for field, value in fields.items()) +
        "--%s--\r\n" % boundary
    )

    content_type = "multipart/form-data; boundary=%s" % boundary

    return body, content_type

@pytest.fixture(scope="session")
def tf_logs(tmpdir_factory):

    import numpy as np
    try:
        import tensorflow.compat.v1 as tf
        tf.disable_v2_behavior()
    except ImportError:
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
    # TODO: Add auth check tests
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

    def test_tensorboard(self):

        content = {"logdir": self.log_dir}
        content_type = {"Content-Type": "application/json"}
        response = self.fetch(
            '/api/tensorboard',
            method='POST',
            body=json.dumps(content),
            headers=content_type)

        response = self.fetch('/api/tensorboard')
        instances = json.loads(response.body.decode())
        assert len(instances) > 0

        response = self.fetch('/api/tensorboard/1')
        instance = json.loads(response.body.decode())
        instance2 = None
        for inst in instances:
            if inst["name"] == instance["name"]:
                instance2 = inst
        assert instance == instance2

        response = self.fetch('/tensorboard/1/#graphs')
        assert response.code == 200

        response = self.fetch(
            '/tensorboard/1/data/plugin/scalars/tags',
            method='GET')
        assert response.code == 200

        body, content_type = encode_multipart_formdata({'tag':'loss', 'runs':['.']})
        response = self.fetch(
            '/tensorboard/1/data/plugin/scalars/scalars_multirun',
            method='POST',
            body=body,
            headers={'Content-Type': content_type})
        assert response.code == 200

        response = self.fetch('/tensorboard/1/data/plugins_listing')
        plugins_list = json.loads(response.body.decode())
        assert plugins_list["graphs"]
        assert plugins_list["scalars"]

        response = self.fetch(
            '/api/tensorboard/1',
            method='DELETE')
        assert response.code == 204

        response = self.fetch('/api/tensorboard/1')
        error_msg = json.loads(response.body.decode())
        assert error_msg["message"].startswith(
            "TensorBoard instance not found:")

    def test_instance_reload(self):
        content = {"logdir": self.log_dir, "reload_interval": 4}
        content_type = {"Content-Type": "application/json"}
        response = self.fetch(
            '/api/tensorboard',
            method='POST',
            body=json.dumps(content),
            headers=content_type)
        instance = json.loads(response.body.decode())
        assert instance is not None
        name = instance["name"]
        reload_time = instance["reload_time"]

        time.sleep(5)
        response = self.fetch('/api/tensorboard/{}'.format(name))
        instance2 = json.loads(response.body.decode())
        assert instance2["reload_time"] != reload_time

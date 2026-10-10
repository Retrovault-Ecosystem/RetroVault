import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from threading import Event
from time import monotonic
from types import SimpleNamespace
import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from ui.library.discovery_jobs import DiscoveryJobs


@pytest.fixture(scope='module')
def app():return QApplication.instance() or QApplication([])


def wait(app, predicate, timeout=3000):
    end=monotonic()+timeout/1000
    while not predicate() and monotonic()<end:
        app.processEvents();QTest.qWait(5)
    assert predicate()


class Controller:
    def __init__(self):self.started=Event();self.release=Event();self.published=[];self.requests=[]
    def discovery_request(self,kind,directory=None):
        self.requests.append(directory);return SimpleNamespace(directory=directory)
    def prepare_discovery(self,request,control):
        self.started.set()
        while not self.release.wait(.01):control.check()
        control.check();return request
    def publish_discovery(self,result):self.published.append(result.directory);return {'games':[]}


def test_cancel_keeps_ui_responsive_and_does_not_publish(app):
    controller=Controller();jobs=DiscoveryJobs(controller);ticks=[]
    timer=QTimer();timer.setInterval(5);timer.timeout.connect(lambda:ticks.append(1));timer.start()
    jobs.request('refresh');wait(app,controller.started.is_set)
    QTest.qWait(50);assert ticks
    start=monotonic();jobs.cancel();wait(app,lambda:not jobs.busy)
    assert monotonic()-start<.5
    assert controller.published==[]
    timer.stop()


def test_only_latest_pending_request_can_publish(app):
    controller=Controller();jobs=DiscoveryJobs(controller)
    jobs.request('refresh','old');wait(app,controller.started.is_set)
    jobs.request('refresh','obsolete');jobs.request('refresh','latest')
    controller.release.set();wait(app,lambda:not jobs.busy)
    assert controller.published==['latest']
    assert controller.requests==['old','latest']


def test_shutdown_retains_worker_until_cancelled(app):
    controller=Controller();jobs=DiscoveryJobs(controller)
    jobs.request('refresh');wait(app,controller.started.is_set)
    assert not jobs.shutdown()
    wait(app,lambda:not jobs.busy)
    assert jobs.shutdown() and not controller.published


def test_worker_error_restores_actions_and_allows_retry(app):
    controller=Controller();jobs=DiscoveryJobs(controller);errors=[];jobs.failed.connect(errors.append)
    prepare=controller.prepare_discovery
    controller.prepare_discovery=lambda *a: (_ for _ in ()).throw(ValueError('broken fixture'))
    jobs.request();wait(app,lambda:not jobs.busy)
    assert errors and not controller.published
    controller.prepare_discovery=prepare;controller.release.set();jobs.request('refresh','retry')
    wait(app,lambda:not jobs.busy)
    assert controller.published==['retry']


def test_commit_announces_non_cancellable_boundary(app):
    controller=Controller();controller.release.set();jobs=DiscoveryJobs(controller);states=[]
    def status(message):
        if 'cannot cancel' in message:
            states.append(jobs.committing)
            jobs.cancel()  # Already accepted: do not falsely report a cancellation.
    jobs.status.connect(status);jobs.request('refresh','accepted');wait(app,lambda:not jobs.busy)
    assert states==[True] and controller.published==['accepted']


def test_repeated_operations_leave_no_running_worker(app):
    controller=Controller();controller.release.set();jobs=DiscoveryJobs(controller)
    for i in range(20):
        jobs.request('refresh',str(i));wait(app,lambda:not jobs.busy)
    assert len(controller.published)==20 and jobs._worker is None
    from PyQt6.QtCore import QCoreApplication,QEvent,QThread
    QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
    assert jobs.findChildren(QThread)==[]

from __future__ import annotations

import io
import json
import logging
import os
import requests
import signal
import subprocess

from kgextractiontoolbox.config import NLP_CONFIG


class Oi5ServerController:
    instance: Oi5ServerController = None

    def __init__(self):
        with open(NLP_CONFIG, "r") as f:
            conf = json.load(f)
        self.jar = conf["openie5.1"]["jar"]
        self.port = conf["openie5.1"]["port"]
        self.proc: subprocess.Popen = None
        self.session = requests.session()

    @staticmethod
    def get():
        if not Oi5ServerController.instance:
            Oi5ServerController.instance = Oi5ServerController()
        return Oi5ServerController.instance

    def start_server(self):
        self.proc = subprocess.Popen(['java', '-jar', self.jar, '--httpPort', str(self.port)], stdout=subprocess.PIPE,
                                     cwd=os.path.dirname(self.jar))
        logging.info("Starting OpenIE5.1, this might take a while...")

        for line in io.TextIOWrapper(self.proc.stdout, encoding="utf8"):
            logging.debug(line)
            if "OpenIE 5.1 is ready" in line:
                return

    def stop_server(self):
        self.proc.send_signal(signal.SIGTERM)
        self.proc = None

    def is_up(self) -> bool:
        if not self.proc:
            return False
        # seems to be the standard way to check for a running process
        try:
            os.kill(self.proc.pid, 0)
        except OSError:
            return False

    def get_extraction(self, sentence: str) -> json:
        try:
            url = f"http://localhost:{self.port}/getExtraction"
            response = self.session.post(url, sentence.encode("utf-8"), timeout=60)
            return json.loads(response.text) if response.text else []
        except Exception as inst:
            print(inst)
            return []

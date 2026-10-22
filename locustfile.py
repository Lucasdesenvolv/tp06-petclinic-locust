import random
import string

from locust import HttpUser, task, between

HOST = "http://localhost:8080"
OWNER_IDS = list(range(1, 11))  # owners 1..10 existem desde o inicio


def random_text(n=8):
    return "".join(random.choices(string.ascii_lowercase, k=n)).capitalize()


def new_owner():
    return {
        "firstName": random_text(),
        "lastName": random_text(),
        "address": f"{random.randint(1, 999)} Test St.",
        "city": random_text(7),
        "telephone": "".join(random.choices(string.digits, k=10)),
    }


class PetClinicUser(HttpUser):
    abstract = True
    host = HOST
    wait_time = between(1, 2)

    def get_owners(self):
        self.client.get("/api/customer/owners", name="GET /owners")

    def get_owner_by_id(self):
        owner_id = random.choice(OWNER_IDS)
        self.client.get(f"/api/customer/owners/{owner_id}", name="GET /owners/{id}")

    def get_vets(self):
        self.client.get("/api/vet/vets", name="GET /vets")

    def post_owner(self):
        self.client.post("/api/customer/owners", json=new_owner(), name="POST /owners")


class LeituraUser(PetClinicUser):
    """Perfil 1 - Leitura: 45% / 35% / 15% / 5%"""

    @task(45)
    def t_get_owners(self):
        self.get_owners()

    @task(35)
    def t_get_owner_by_id(self):
        self.get_owner_by_id()

    @task(15)
    def t_get_vets(self):
        self.get_vets()

    @task(5)
    def t_post_owner(self):
        self.post_owner()


class EscritaUser(PetClinicUser):
    """Perfil 2 - Escrita: 20% / 20% / 20% / 40%"""

    @task(20)
    def t_get_owners(self):
        self.get_owners()

    @task(20)
    def t_get_owner_by_id(self):
        self.get_owner_by_id()

    @task(20)
    def t_get_vets(self):
        self.get_vets()

    @task(40)
    def t_post_owner(self):
        self.post_owner()


# --- Aquecimento: descarta as estatisticas coletadas ate WARMUP_SECONDS ---
import os

import gevent
from locust import events

WARMUP_SECONDS = int(os.environ.get("WARMUP_SECONDS", "0"))


@events.test_start.add_listener
def _schedule_warmup_reset(environment, **kwargs):
    if WARMUP_SECONDS <= 0:
        return

    def _reset():
        gevent.sleep(WARMUP_SECONDS)
        environment.stats.reset_all()
        print(f"[warmup] {WARMUP_SECONDS}s concluidos: estatisticas zeradas")

    gevent.spawn(_reset)

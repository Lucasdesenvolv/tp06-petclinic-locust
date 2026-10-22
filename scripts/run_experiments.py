"""Executa o experimento: 2 perfis x 3 cenarios x N repeticoes."""
import argparse
import csv
import os
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "http://localhost:8080"
SPAWN_RATE = 5
MONITORED = ["api-gateway", "customers-service", "vets-service"]
SCENARIOS = {"A": 30, "B": 80, "C": 150}
PROFILES = {"leitura": "LeituraUser", "escrita": "EscritaUser"}
MAX_ATTEMPTS = 2
INVALID_FAIL_RATIO = 0.9  # acima disso a execucao e considerada problema de ambiente


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def http_ok(path):
    try:
        with urllib.request.urlopen(BASE_URL + path, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def wait_until_ready(timeout=300, needed=10):
    start = time.time()
    streak = 0
    while time.time() - start < timeout:
        if http_ok("/api/customer/owners/1") and http_ok("/api/vet/vets"):
            streak += 1
            if streak >= needed:
                return True
        else:
            streak = 0
        time.sleep(2)
    return False


def reset_environment():
    log("Reiniciando customers-service e api-gateway...")
    subprocess.run(["docker", "restart", "customers-service", "api-gateway"],
                   check=True, stdout=subprocess.DEVNULL)
    if not wait_until_ready():
        raise RuntimeError("servicos nao ficaram prontos apos o restart")
    time.sleep(5)


def failure_ratio(stats_path):
    if not stats_path.exists():
        return 1.0
    with open(stats_path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("Name") == "Aggregated":
                total = int(row["Request Count"])
                fails = int(row["Failure Count"])
                return fails / total if total else 1.0
    return 1.0


class CpuMonitor(threading.Thread):
    def __init__(self, path):
        super().__init__(daemon=True)
        self.path = path
        self.stop_event = threading.Event()

    def run(self):
        t0 = time.time()
        cmd = ["docker", "stats", "--no-stream", "--format",
               "{{.Name}};{{.CPUPerc}};{{.MemUsage}}"] + MONITORED
        with open(self.path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["elapsed_s", "container", "cpu_percent", "mem_usage"])
            while not self.stop_event.is_set():
                try:
                    out = subprocess.run(cmd, capture_output=True, text=True,
                                         timeout=30).stdout
                except Exception:
                    time.sleep(1)
                    continue
                elapsed = round(time.time() - t0, 1)
                for line in out.strip().splitlines():
                    parts = line.split(";")
                    if len(parts) == 3:
                        w.writerow([elapsed, parts[0], parts[1].rstrip("%"), parts[2]])
                f.flush()


def run_one(profile, scenario, rep, args, outdir):
    users = SCENARIOS[scenario]
    name = f"{profile}_{scenario}_r{rep:02d}"
    done = outdir / f"{name}.done"
    if done.exists():
        log(f"{name}: ja concluida, pulando")
        return

    for attempt in range(1, MAX_ATTEMPTS + 1):
        for old in outdir.glob(f"{name}_*"):
            old.unlink()
        try:
            reset_environment()
        except Exception as e:
            log(f"{name}: falha no reset ({e}), tentativa {attempt}")
            continue

        log(f"INICIANDO {name} ({users} usuarios, {args.total}s, "
            f"aquecimento {args.warmup}s, tentativa {attempt})")
        monitor = CpuMonitor(outdir / f"{name}_cpu.csv")
        cmd = [sys.executable, "-m", "locust", "-f", str(ROOT / "locustfile.py"),
               PROFILES[profile], "--headless", "-u", str(users), "-r", str(SPAWN_RATE),
               "-t", f"{args.total}s", "--csv", str(outdir / name), "--only-summary"]
        env = dict(os.environ, WARMUP_SECONDS=str(args.warmup))

        t_start = datetime.now()
        monitor.start()
        with open(outdir / f"{name}_locust.log", "w") as lf:
            subprocess.run(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT, cwd=ROOT)
        monitor.stop_event.set()
        monitor.join(timeout=40)

        ratio = failure_ratio(outdir / f"{name}_stats.csv")
        status = "ok" if ratio < INVALID_FAIL_RATIO else "invalida"
        with open(outdir / "runs_log.csv", "a", newline="") as f:
            csv.writer(f).writerow([name, profile, scenario, rep, users,
                                    t_start.isoformat(timespec="seconds"),
                                    datetime.now().isoformat(timespec="seconds"),
                                    attempt, f"{ratio:.4f}", status])
        if status == "ok":
            done.write_text("ok")
            log(f"{name}: OK (taxa de falhas {ratio:.1%})")
            return
        log(f"{name}: INVALIDA (falhas {ratio:.0%}), problema de ambiente")

    log(f"{name}: desistindo apos {MAX_ATTEMPTS} tentativas")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=10)
    p.add_argument("--total", type=int, default=420,
                   help="duracao total em segundos (aquecimento + medicao)")
    p.add_argument("--warmup", type=int, default=60)
    p.add_argument("--scenarios", default="A,B,C")
    p.add_argument("--profiles", default="leitura,escrita")
    p.add_argument("--outdir", default="results/raw")
    args = p.parse_args()

    outdir = ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    jobs = [(prof, sc, rep)
            for rep in range(1, args.reps + 1)
            for sc in args.scenarios.split(",")
            for prof in args.profiles.split(",")]
    pending = [j for j in jobs if not (outdir / f"{j[0]}_{j[1]}_r{j[2]:02d}.done").exists()]
    est_h = len(pending) * (args.total + 90) / 3600
    log(f"{len(jobs)} execucoes no total, {len(pending)} pendentes (~{est_h:.1f} h)")

    for prof, sc, rep in jobs:
        run_one(prof, sc, rep, args, outdir)
    log("TUDO CONCLUIDO")


if __name__ == "__main__":
    main()

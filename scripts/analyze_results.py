"""Analise dos resultados do TP06: agrega as repeticoes, gera tabelas e graficos.

O aquecimento (60 s) ja foi descartado na coleta: o locustfile zera as estatisticas
apos WARMUP_SECONDS, entao os *_stats.csv contem apenas a janela medida.
Para o CPU, descartamos aqui as amostras dos primeiros CPU_CUTOFF_S segundos.
"""
import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
USERS = {"A": 30, "B": 80, "C": 150}
SCEN_LABEL = {"A": "A - Leve", "B": "B - Moderado", "C": "C - Elevado"}
PROFILES = ["leitura", "escrita"]
PROFILE_LABEL = {"leitura": "Perfil 1 - Leitura", "escrita": "Perfil 2 - Escrita"}
SERVICES = ["api-gateway", "customers-service", "vets-service"]
ENDPOINTS = ["GET /owners", "GET /owners/{id}", "GET /vets", "POST /owners"]
CPU_CUTOFF_S = 65  # 60 s de aquecimento + ~5 s de partida do Locust
COLORS = {"leitura": "#1f77b4", "escrita": "#d62728"}
STATS_RE = re.compile(r"^(leitura|escrita)_([ABC])_r(\d+)_stats\.csv$")
CPU_RE = re.compile(r"^(leitura|escrita)_([ABC])_r(\d+)_cpu\.csv$")


def load_stats(raw):
    agg, ep = [], []
    for f in sorted(raw.glob("*_stats.csv")):
        m = STATS_RE.match(f.name)
        if not m:
            continue
        profile, scen, rep = m.group(1), m.group(2), int(m.group(3))
        for _, r in pd.read_csv(f).iterrows():
            total = float(r["Request Count"])
            fails = float(r["Failure Count"])
            row = {
                "profile": profile, "scenario": scen, "users": USERS[scen], "rep": rep,
                "name": r["Name"], "requests": total, "failures": fails,
                "avg_ms": float(r["Average Response Time"]),
                "p95_ms": float(r["95%"]),
                "rps": float(r["Requests/s"]),
                "rps_ok": float(r["Requests/s"]) - float(r["Failures/s"]),
                "fail_pct": 100.0 * fails / total if total else float("nan"),
            }
            (agg if r["Name"] == "Aggregated" else ep).append(row)
    return pd.DataFrame(agg), pd.DataFrame(ep)


def load_cpu(raw):
    rows = []
    for f in sorted(raw.glob("*_cpu.csv")):
        m = CPU_RE.match(f.name)
        if not m:
            continue
        df = pd.read_csv(f)
        df = df[df["elapsed_s"] >= CPU_CUTOFF_S].copy()
        df["cpu_percent"] = pd.to_numeric(df["cpu_percent"], errors="coerce")
        df["mem_mib"] = pd.to_numeric(
            df["mem_usage"].astype(str).str.extract(r"([\d.]+)MiB")[0], errors="coerce")
        for cont, g in df.groupby("container"):
            rows.append({
                "profile": m.group(1), "scenario": m.group(2), "rep": int(m.group(3)),
                "container": cont, "cpu_mean": g["cpu_percent"].mean(),
                "cpu_max": g["cpu_percent"].max(), "mem_mean": g["mem_mib"].mean(),
            })
    return pd.DataFrame(rows)


def md_table(df, fmt=None):
    fmt = fmt or {}
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append(fmt.get(c, "{:.1f}").format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def pm(mean, std):
    return f"{mean:.1f} \u00b1 {0 if pd.isna(std) else std:.1f}"


def scenario_summary(agg):
    rows = []
    for (p, s), g in agg.groupby(["profile", "scenario"]):
        rows.append({
            "Perfil": p, "Cen\u00e1rio": SCEN_LABEL[s], "Usu\u00e1rios": USERS[s], "Reps": len(g),
            "Tempo m\u00e9dio (ms)": pm(g.avg_ms.mean(), g.avg_ms.std()),
            "P95 (ms)": pm(g.p95_ms.mean(), g.p95_ms.std()),
            "Vaz\u00e3o (req/s)": pm(g.rps.mean(), g.rps.std()),
            "Vaz\u00e3o sem falhas (req/s)": pm(g.rps_ok.mean(), g.rps_ok.std()),
            "Total de req.": f"{g.requests.mean():.0f}",
            "Falhas (%)": pm(g.fail_pct.mean(), g.fail_pct.std()),
            "_u": USERS[s], "_p": PROFILES.index(p),
        })
    out = pd.DataFrame(rows).sort_values(["_p", "_u"]).drop(columns=["_u", "_p"])
    return out.reset_index(drop=True)


def endpoint_summary(ep):
    rows = []
    for (p, s, n), g in ep.groupby(["profile", "scenario", "name"]):
        rows.append({
            "Perfil": p, "Cen\u00e1rio": s, "Opera\u00e7\u00e3o": n,
            "Tempo m\u00e9dio (ms)": g.avg_ms.mean(), "P95 (ms)": g.p95_ms.mean(),
            "Falhas (%)": g.fail_pct.mean(), "Req. (m\u00e9dia)": g.requests.mean(),
        })
    df = pd.DataFrame(rows)
    df["_o"] = df["Opera\u00e7\u00e3o"].map({e: i for i, e in enumerate(ENDPOINTS)})
    df["_p"] = df["Perfil"].map({p: i for i, p in enumerate(PROFILES)})
    return df.sort_values(["_p", "Cen\u00e1rio", "_o"]).drop(columns=["_o", "_p"]).reset_index(drop=True)


def cpu_summary(cpu):
    rows = []
    for (p, s, c), g in cpu.groupby(["profile", "scenario", "container"]):
        rows.append({
            "Perfil": p, "Cen\u00e1rio": s, "Servi\u00e7o": c,
            "CPU m\u00e9dia (%)": g.cpu_mean.mean(), "CPU m\u00e1x. m\u00e9dia (%)": g.cpu_max.mean(),
            "Mem\u00f3ria m\u00e9dia (MiB)": g.mem_mean.mean(),
        })
    return pd.DataFrame(rows).sort_values(["Perfil", "Cen\u00e1rio", "Servi\u00e7o"]).reset_index(drop=True)


def line_chart(agg, col, ylabel, title, path, extra=None):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for p in PROFILES:
        g = agg[agg.profile == p].groupby("users")[col].agg(["mean", "std"]).reset_index()
        ax.errorbar(g["users"], g["mean"], yerr=g["std"].fillna(0), marker="o", capsize=3,
                    color=COLORS[p], label=PROFILE_LABEL[p])
        if extra:
            e = agg[agg.profile == p].groupby("users")[extra].mean().reset_index()
            ax.plot(e["users"], e[extra], marker="s", linestyle="--", color=COLORS[p],
                    alpha=0.6, label=f"{PROFILE_LABEL[p]} (sem falhas)")
    ax.set_xticks(list(USERS.values()))
    ax.set_xlabel("Usu\u00e1rios simult\u00e2neos")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def failure_chart(agg, path):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    width = 0.35
    xs = range(len(USERS))
    for i, p in enumerate(PROFILES):
        vals = [agg[(agg.profile == p) & (agg.scenario == s)].fail_pct.mean() for s in USERS]
        errs = [agg[(agg.profile == p) & (agg.scenario == s)].fail_pct.std() for s in USERS]
        ax.bar([x + (i - 0.5) * width for x in xs], vals, width,
               yerr=[0 if pd.isna(e) else e for e in errs], capsize=3,
               color=COLORS[p], label=PROFILE_LABEL[p])
    ax.set_xticks(list(xs))
    ax.set_xticklabels([SCEN_LABEL[s] for s in USERS])
    ax.set_ylabel("Taxa de falhas (%)")
    ax.set_title("Taxa de falhas por cen\u00e1rio")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def cpu_chart(cpu, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    width = 0.25
    for ax, p in zip(axes, PROFILES):
        for i, svc in enumerate(SERVICES):
            vals = [cpu[(cpu.profile == p) & (cpu.scenario == s) & (cpu.container == svc)]
                    .cpu_mean.mean() for s in USERS]
            ax.bar([x + (i - 1) * width for x in range(len(USERS))], vals, width, label=svc)
        ax.set_xticks(range(len(USERS)))
        ax.set_xticklabels([SCEN_LABEL[s] for s in USERS])
        ax.set_title(PROFILE_LABEL[p])
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel("CPU m\u00e9dia (%) - 100% = 1 n\u00facleo")
    axes[0].legend()
    fig.suptitle("Consumo de CPU por servi\u00e7o")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def endpoint_chart(ep, col, ylabel, title, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    width = 0.2
    for ax, p in zip(axes, PROFILES):
        for i, name in enumerate(ENDPOINTS):
            vals = [ep[(ep.profile == p) & (ep.scenario == s) & (ep.name == name)][col].mean()
                    for s in USERS]
            ax.bar([x + (i - 1.5) * width for x in range(len(USERS))], vals, width, label=name)
        ax.set_xticks(range(len(USERS)))
        ax.set_xticklabels([SCEN_LABEL[s] for s in USERS])
        ax.set_title(PROFILE_LABEL[p])
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel(ylabel)
    axes[0].legend()
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def timeline_chart(raw, name, path):
    f = raw / f"{name}_stats_history.csv"
    if not f.exists():
        return
    h = pd.read_csv(f)
    h = h[h["Name"] == "Aggregated"].copy()
    h["t"] = h["Timestamp"] - h["Timestamp"].min()
    h = h[h["Requests/s"] > 0]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(h["t"], h["Requests/s"], label="Requisi\u00e7\u00f5es/s", color="#1f77b4")
    ax.plot(h["t"], h["Failures/s"], label="Falhas/s", color="#d62728")
    ax.axvline(60, color="gray", linestyle=":", label="fim do aquecimento")
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("req/s")
    ax.set_title(f"Evolu\u00e7\u00e3o ao longo da execu\u00e7\u00e3o: {name}")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="results/raw")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    raw, out = ROOT / args.raw, ROOT / args.out
    charts = out / "charts"
    charts.mkdir(parents=True, exist_ok=True)

    agg, ep = load_stats(raw)
    cpu = load_cpu(raw)
    if agg.empty:
        raise SystemExit(f"Nenhum *_stats.csv encontrado em {raw}")
    print(f"{len(agg)} execucoes lidas, {len(cpu)} registros de CPU")

    runs = agg.drop(columns=["name"]).sort_values(["profile", "scenario", "rep"])
    runs.to_csv(out / "runs_summary.csv", index=False)
    t1, t2, t3 = scenario_summary(agg), endpoint_summary(ep), cpu_summary(cpu)
    t1.to_csv(out / "summary_by_scenario.csv", index=False)
    t2.to_csv(out / "summary_by_endpoint.csv", index=False)
    t3.to_csv(out / "summary_cpu.csv", index=False)

    with open(out / "tables.md", "w", encoding="utf-8") as f:
        f.write("## Tabela 1 - M\u00e9tricas por perfil e cen\u00e1rio (m\u00e9dia \u00b1 desvio padr\u00e3o das repeti\u00e7\u00f5es)\n\n")
        f.write(md_table(t1) + "\n\n")
        f.write("## Tabela 2 - M\u00e9tricas por opera\u00e7\u00e3o (m\u00e9dia das repeti\u00e7\u00f5es)\n\n")
        f.write(md_table(t2) + "\n\n")
        f.write("## Tabela 3 - CPU e mem\u00f3ria por servi\u00e7o (m\u00e9dia das repeti\u00e7\u00f5es)\n\n")
        f.write(md_table(t3) + "\n")

    line_chart(agg, "avg_ms", "Tempo m\u00e9dio de resposta (ms)",
               "Tempo m\u00e9dio de resposta x usu\u00e1rios", charts / "tempo_medio.png")
    line_chart(agg, "p95_ms", "P95 (ms)", "Tempo de resposta P95 x usu\u00e1rios",
               charts / "p95.png")
    line_chart(agg, "rps", "Vaz\u00e3o (req/s)", "Vaz\u00e3o x usu\u00e1rios", charts / "vazao.png",
               extra="rps_ok")
    failure_chart(agg, charts / "falhas.png")
    if not cpu.empty:
        cpu_chart(cpu, charts / "cpu.png")
    endpoint_chart(ep, "p95_ms", "P95 (ms)", "P95 por opera\u00e7\u00e3o", charts / "p95_por_operacao.png")
    endpoint_chart(ep, "fail_pct", "Falhas (%)", "Taxa de falhas por opera\u00e7\u00e3o",
                   charts / "falhas_por_operacao.png")
    for n in ("escrita_B_r01", "escrita_C_r01"):
        timeline_chart(raw, n, charts / f"timeline_{n}.png")

    print("Arquivos gerados em", out)
    print(t1.to_string(index=False))


if __name__ == "__main__":
    main()

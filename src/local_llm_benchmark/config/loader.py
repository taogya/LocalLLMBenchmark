"""Configuration & Task Catalog (TASK-00007-01, TASK-00013-02).

COMP-00007 (Configuration Loader) と COMP-00008 (Task Catalog) を提供する。
v1 では TOML (`tomllib` 標準) でユーザー素材を読み込み、整合性検証
(CFG-00501..00505 のうち Phase 1 範囲) を行う。

物理スキーマは設計書では確定していないため、本実装で初めて確定する
(設計上の概念のみが正本)。具体キー名は本ファイル内コメントで管理する
(.github/copilot-instructions.md の方針)。

CFG-00004 「1 ファイル 1 概念」に従い、種類別ファイルを別ディレクトリ
で受け取る構成を既定とする。
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from ..models import (
    Case,
    GenerationConditions,
    ModelCandidate,
    ProviderEndpoint,
    RunPlan,
    ScorerSpec,
    TaskProfile,
)


class ConfigurationError(Exception):
    """設定読込・整合性検証で検出した不整合 (FLW-00102, CFG-00402 ほか)."""


# ---- Task Catalog (COMP-00008) ---------------------------------------------


@dataclass(frozen=True)
class TaskCatalog:
    """TaskProfile 集合の提供者 (COMP-00008).

    name -> TaskProfile の辞書を内包する。
    """

    profiles: Mapping[str, TaskProfile]

    def resolve(self, names: Iterable[str]) -> list[TaskProfile]:
        """名称列から TaskProfile を解決する。未登録は ConfigurationError."""
        out: list[TaskProfile] = []
        for n in names:
            if n not in self.profiles:
                raise ConfigurationError(f"未登録の Task Profile を参照: {n}")
            out.append(self.profiles[n])
        return out


def _load_toml(path: Path) -> Mapping[str, object]:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"設定ファイルが見つからない: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"TOML 解析失敗 ({path}): {exc}") from exc


def _require(d: Mapping[str, object], key: str, where: str) -> object:
    if key not in d:
        raise ConfigurationError(f"必須キー '{key}' が無い ({where})")
    return d[key]


def _parse_task_profile(data: Mapping[str, object], src: Path) -> TaskProfile:
    """物理スキーマ (本実装で確定):

        [task_profile]
        name = "qa-basic"
        purpose = "短答 QA"
        description = "..."
        [task_profile.scorer]
        name = "exact_match"
        args = { normalize_whitespace = true }   # 任意
        [[task_profile.cases]]
        name = "case-1"
        input = "..."
        expected_output = "..."
    """
    tp = _require(data, "task_profile", str(src))
    if not isinstance(tp, dict):
        raise ConfigurationError(f"[task_profile] テーブルが不正: {src}")
    name = str(_require(tp, "name", str(src)))
    purpose = str(_require(tp, "purpose", str(src)))
    description = tp.get("description")
    scorer_d = _require(tp, "scorer", str(src))
    if not isinstance(scorer_d, dict):
        raise ConfigurationError(f"[task_profile.scorer] が不正: {src}")
    scorer = ScorerSpec(
        name=str(_require(scorer_d, "name", str(src))),
        args=dict(scorer_d.get("args") or {}),
    )
    cases_raw = _require(tp, "cases", str(src))
    if not isinstance(cases_raw, list) or not cases_raw:
        # DAT-00101: 最低 1 件
        raise ConfigurationError(
            f"Task Profile は最低 1 件の Case を持つ必要がある (DAT-00101): {src}"
        )
    cases: list[Case] = []
    for c in cases_raw:
        if not isinstance(c, dict):
            raise ConfigurationError(f"case エントリが不正: {src}")
        cases.append(
            Case(
                name=str(_require(c, "name", str(src))),
                input_text=str(_require(c, "input", str(src))),
                expected_output=(None if c.get("expected_output") is None
                                 else str(c["expected_output"])),
            )
        )
    return TaskProfile(
        name=name,
        purpose=purpose,
        description=None if description is None else str(description),
        scorer=scorer,
        cases=tuple(cases),
    )


def load_task_catalog(task_profile_dir: Path) -> TaskCatalog:
    """ディレクトリ配下の `*.toml` を Task Profile として読み込む (COMP-00008).

    1 ファイル 1 TaskProfile を前提 (CFG-00004)。
    """
    if not task_profile_dir.is_dir():
        raise ConfigurationError(
            f"Task Profile ディレクトリが存在しない: {task_profile_dir}"
        )
    profiles: dict[str, TaskProfile] = {}
    for path in sorted(task_profile_dir.glob("*.toml")):
        data = _load_toml(path)
        tp = _parse_task_profile(data, path)
        if tp.name in profiles:
            raise ConfigurationError(f"Task Profile 名が重複: {tp.name}")
        profiles[tp.name] = tp
    return TaskCatalog(profiles=profiles)


def load_task_profile(path: Path) -> TaskProfile:
    """単一の Task Profile 定義を読み込む (TASK-00013-02)."""
    return _parse_task_profile(_load_toml(path), path)


# ---- Model / Provider 定義 -------------------------------------------------


def _parse_model_candidates(
    data: Mapping[str, object], src: Path
) -> dict[str, ModelCandidate]:
    """物理スキーマ:

        [[model_candidate]]
        name = "qwen2:1.5b"
        provider_kind = "ollama"
        provider_model_ref = "qwen2:1.5b"
        label = "qwen2 small"
    """
    raw = data.get("model_candidate")
    if not isinstance(raw, list) or not raw:
        raise ConfigurationError(
            f"[[model_candidate]] が空、または不正な形式: {src}"
        )
    out: dict[str, ModelCandidate] = {}
    for entry in raw:
        if not isinstance(entry, dict):
            raise ConfigurationError(f"model_candidate エントリが不正: {src}")
        mc = ModelCandidate(
            name=str(_require(entry, "name", str(src))),
            provider_kind=str(_require(entry, "provider_kind", str(src))),
            provider_model_ref=str(
                _require(entry, "provider_model_ref", str(src))
            ),
            label=(
                None if entry.get("label") is None
                else str(entry["label"])
            ),
        )
        if mc.name in out:
            raise ConfigurationError(f"Model Candidate 名が重複: {mc.name}")
        out[mc.name] = mc
    return out


def load_model_candidates(path: Path) -> dict[str, ModelCandidate]:
    return _parse_model_candidates(_load_toml(path), path)


def _parse_provider_endpoints(
    data: Mapping[str, object], src: Path
) -> dict[str, ProviderEndpoint]:
    """物理スキーマ:

        [[provider]]
        kind = "ollama"
        host = "localhost"
        port = 11434
        timeout_seconds = 120

    認証情報の平文格納は禁止 (CFG-00402)。Phase 1 では Ollama のみで
    認証要素を持たない想定だが、未知キー `api_key` 等の混入を検出
    した場合は失敗させる。
    """
    raw = data.get("provider")
    if not isinstance(raw, list) or not raw:
        raise ConfigurationError(
            f"[[provider]] が空、または不正な形式: {src}"
        )
    forbidden = {"api_key", "token", "password", "secret"}
    out: dict[str, ProviderEndpoint] = {}
    for entry in raw:
        if not isinstance(entry, dict):
            raise ConfigurationError(f"provider エントリが不正: {src}")
        # CFG-00402 認証情報の平文を検出
        leaked = forbidden.intersection(entry.keys())
        if leaked:
            raise ConfigurationError(
                f"認証情報を平文で保持している (CFG-00402): {sorted(leaked)} in {src}"
            )
        kind = str(_require(entry, "kind", str(src)))
        ep = ProviderEndpoint(
            kind=kind,
            host=str(entry.get("host", "localhost")),
            port=int(entry.get("port", 11434)),
            timeout_seconds=float(entry.get("timeout_seconds", 120.0)),
        )
        if kind in out:
            raise ConfigurationError(f"provider 種別が重複: {kind}")
        out[kind] = ep
    return out


def load_provider_endpoints(path: Path) -> dict[str, ProviderEndpoint]:
    return _parse_provider_endpoints(_load_toml(path), path)


# ---- Run 設定 (CFG-00107) --------------------------------------------------


@dataclass(frozen=True)
class RunConfig:
    """Run 設定の物理表現 (CFG-00107 / CFG-00206).

    Loader の検証で 1 Run = 1 Model (FUN-00207, ARCH-00207) を強制する。
    """

    model_candidate_name: str
    task_profile_names: tuple[str, ...]
    n_trials: int
    conditions: GenerationConditions
    store_root: Path | None  # None なら CLI 既定にフォールバック


def _parse_run_config(data: Mapping[str, object], src: Path) -> RunConfig:
    """物理スキーマ:

        [run]
        model_candidate = "qwen2:1.5b"
        task_profiles = ["qa-basic"]
        n_trials = 3
        store_root = "tmp/results"

        [run.generation]
        temperature = 0.0
        seed = 42
        max_tokens = 256
    """
    rc = _require(data, "run", str(src))
    if not isinstance(rc, dict):
        raise ConfigurationError(f"[run] テーブルが不正: {src}")
    model_field = _require(rc, "model_candidate", str(src))
    # CLI-00106: 複数 Model 指定はエラー
    if isinstance(model_field, list):
        raise ConfigurationError(
            "複数 Model Candidate 指定は禁止 (1 Run = 1 Model: FUN-00207)。"
            " compare サブコマンドの利用を検討してください。"
        )
    if not isinstance(model_field, str):
        raise ConfigurationError(f"model_candidate は文字列で指定する: {src}")
    tp_field = _require(rc, "task_profiles", str(src))
    if not isinstance(tp_field, list) or not tp_field:
        raise ConfigurationError(f"task_profiles は 1 件以上の配列: {src}")
    n_trials_value = _require(rc, "n_trials", str(src))
    if not isinstance(n_trials_value, int):
        raise ConfigurationError(f"n_trials は整数で指定する: {src}")
    n_trials = int(n_trials_value)
    if n_trials < 1:
        raise ConfigurationError(f"n_trials は 1 以上: {src}")
    gen_d = rc.get("generation") or {}
    if not isinstance(gen_d, dict):
        raise ConfigurationError(f"[run.generation] が不正: {src}")
    conditions = GenerationConditions(
        temperature=(None if gen_d.get("temperature") is None
                     else float(gen_d["temperature"])),
        seed=(None if gen_d.get("seed") is None else int(gen_d["seed"])),
        max_tokens=(None if gen_d.get("max_tokens") is None
                    else int(gen_d["max_tokens"])),
    )
    store_root = rc.get("store_root")
    return RunConfig(
        model_candidate_name=model_field,
        task_profile_names=tuple(str(x) for x in tp_field),
        n_trials=n_trials,
        conditions=conditions,
        store_root=None if store_root is None else Path(str(store_root)),
    )


def load_run_config(path: Path) -> RunConfig:
    return _parse_run_config(_load_toml(path), path)


# ---- Comparison 設定 (CFG-00207, TASK-00007-02) ----------------------------


@dataclass(frozen=True)
class ComparisonConfig:
    """Comparison 設定の物理表現 (CFG-00207).

    Loader 側では DAT-00108 (2 件以上) のみ静的に検証する。Run 識別子の
    実在性 (CFG-00506) は Run Comparator 実行時に Result Store 参照で
    検証する。
    """

    run_ids: tuple[str, ...]
    ranking_axis_default: str  # "quality" / "speed" / "integrated"
    w_quality: float
    w_speed: float
    store_root: Path | None


_VALID_AXES = ("quality", "speed", "integrated")


def _parse_comparison_config(
    data: Mapping[str, object], src: Path
) -> ComparisonConfig:
    """物理スキーマ (本実装で確定):

        [comparison]
        runs = ["run-...-A", "run-...-B"]
        ranking_axis_default = "integrated"   # 任意
        store_root = "tmp/results"            # 任意

        [comparison.weights]
        w_quality = 0.7   # 任意 (既定 SCR-00806)
        w_speed   = 0.3   # 任意 (既定 SCR-00807)
    """
    cmp = _require(data, "comparison", str(src))
    if not isinstance(cmp, dict):
        raise ConfigurationError(f"[comparison] テーブルが不正: {src}")
    runs_field = _require(cmp, "runs", str(src))
    if not isinstance(runs_field, list):
        raise ConfigurationError(f"comparison.runs は配列で指定する: {src}")
    run_ids = tuple(str(x) for x in runs_field)
    # CFG-00506 / DAT-00108: 2 件以上を Loader でも検証
    if len(set(run_ids)) < 2:
        raise ConfigurationError(
            "comparison.runs は重複を除いて 2 件以上必要"
            " (DAT-00108 / CFG-00506)"
        )
    axis_default = str(cmp.get("ranking_axis_default", "integrated"))
    if axis_default not in _VALID_AXES:
        raise ConfigurationError(
            f"comparison.ranking_axis_default は {_VALID_AXES} のいずれか: {src}"
        )
    weights = cmp.get("weights") or {}
    if not isinstance(weights, dict):
        raise ConfigurationError(f"[comparison.weights] が不正: {src}")
    w_quality = float(weights.get("w_quality", 0.7))  # SCR-00806 既定
    w_speed = float(weights.get("w_speed", 0.3))  # SCR-00807 既定
    if w_quality < 0 or w_speed < 0:
        raise ConfigurationError(
            "comparison.weights は 0 以上の浮動小数を指定する (SCR-00808)"
        )
    if w_quality + w_speed <= 0:
        raise ConfigurationError(
            "comparison.weights の合計が 0 では統合スコアを算出できない"
        )
    store_root = cmp.get("store_root")
    return ComparisonConfig(
        run_ids=run_ids,
        ranking_axis_default=axis_default,
        w_quality=w_quality,
        w_speed=w_speed,
        store_root=None if store_root is None else Path(str(store_root)),
    )


def load_comparison_config(path: Path) -> ComparisonConfig:
    return _parse_comparison_config(_load_toml(path), path)


# ---- Run 計画の組み立て -----------------------------------------------------


def assemble_run_plan(
    run_config: RunConfig,
    catalog: TaskCatalog,
    models: Mapping[str, ModelCandidate],
    providers: Mapping[str, ProviderEndpoint],
) -> RunPlan:
    """RunConfig + 各 Catalog から RunPlan を組み立てる (FLW-00005)."""
    if run_config.model_candidate_name not in models:
        raise ConfigurationError(
            f"未登録の Model Candidate を参照: {run_config.model_candidate_name}"
        )
    model = models[run_config.model_candidate_name]
    if model.provider_kind not in providers:
        # CFG-00502
        raise ConfigurationError(
            f"未登録の provider 種別: {model.provider_kind}"
        )
    profiles = catalog.resolve(run_config.task_profile_names)
    return RunPlan(
        model_candidate=model,
        task_profiles=tuple(profiles),
        n_trials=run_config.n_trials,
        conditions=run_config.conditions,
        provider_endpoint=providers[model.provider_kind],
    )


# ---- ディレクトリ規約 ------------------------------------------------------


@dataclass(frozen=True)
class ConfigBundle:
    """ユーザー設定一式 (Configuration Loader 集約).

    CFG-00302: 「ツール本体側既定 / ユーザー指定外部」のどちらから読んだ
    かはこの型のフィールドではなく Run メタに記録する責務 (Phase 1 では
    `source_root` を保持し Coordinator 側で記録する)。
    """

    source_root: Path
    catalog: TaskCatalog
    models: Mapping[str, ModelCandidate]
    providers: Mapping[str, ProviderEndpoint]


def load_config_bundle(config_dir: Path) -> ConfigBundle:
    """既定ディレクトリ構成からまとめて読み込む.

    既定ディレクトリ構成 (1 ファイル 1 概念: CFG-00004):

        <config_dir>/
            task_profiles/*.toml   # CFG-00101
            model_candidates.toml  # CFG-00102
            providers.toml         # CFG-00104
    """
    if not config_dir.is_dir():
        raise ConfigurationError(f"設定ディレクトリが存在しない: {config_dir}")
    catalog = load_task_catalog(config_dir / "task_profiles")
    models = load_model_candidates(config_dir / "model_candidates.toml")
    providers = load_provider_endpoints(config_dir / "providers.toml")
    return ConfigBundle(
        source_root=config_dir.resolve(),
        catalog=catalog,
        models=models,
        providers=providers,
    )


def _classify_config_file(
    data: Mapping[str, object],
    src: Path,
) -> str:
    kinds: list[str] = []
    if "task_profile" in data:
        kinds.append("task_profile")
    if "model_candidate" in data:
        kinds.append("model_candidates")
    if "provider" in data:
        kinds.append("providers")
    if "run" in data:
        kinds.append("run")
    if "comparison" in data:
        kinds.append("comparison")
    if len(kinds) != 1:
        raise ConfigurationError(
            "設定ファイル種別を一意に判定できない:"
            f" {src} kinds={kinds or 'none'}"
        )
    return kinds[0]


def _resolve_lint_support_path(
    explicit: Path | None,
    default: Path,
    *,
    label: str,
) -> Path:
    if explicit is not None:
        return explicit
    if default.exists():
        return default
    raise ConfigurationError(
        f"{label} の補助設定ソースを解決できない: {default}"
    )


def _load_lint_bundle(
    target: Path,
    *,
    config_dir: Path | None,
    task_profile_dir: Path | None,
    model_candidates_path: Path | None,
    providers_path: Path | None,
) -> ConfigBundle:
    base_dir = config_dir or target.parent
    resolved_task_profile_dir = _resolve_lint_support_path(
        task_profile_dir,
        base_dir / "task_profiles",
        label="Task Profile",
    )
    resolved_model_candidates_path = _resolve_lint_support_path(
        model_candidates_path,
        base_dir / "model_candidates.toml",
        label="Model Candidate",
    )
    resolved_providers_path = _resolve_lint_support_path(
        providers_path,
        base_dir / "providers.toml",
        label="Provider",
    )
    return ConfigBundle(
        source_root=base_dir.resolve(),
        catalog=load_task_catalog(resolved_task_profile_dir),
        models=load_model_candidates(resolved_model_candidates_path),
        providers=load_provider_endpoints(resolved_providers_path),
    )


def load_support_bundle(
    target: Path,
    *,
    config_dir: Path | None = None,
    task_profile_dir: Path | None = None,
    model_candidates_path: Path | None = None,
    providers_path: Path | None = None,
) -> ConfigBundle:
    """単一ファイル検証や dry-run 用の補助設定ソースを解決する."""
    return _load_lint_bundle(
        target,
        config_dir=config_dir,
        task_profile_dir=task_profile_dir,
        model_candidates_path=model_candidates_path,
        providers_path=providers_path,
    )


def lint_config_target(
    target: Path,
    *,
    config_dir: Path | None = None,
    task_profile_dir: Path | None = None,
    model_candidates_path: Path | None = None,
    providers_path: Path | None = None,
    store_root: Path | None = None,
) -> list[CheckIssue]:
    """`config lint` の主入力を静的検証する (TASK-00013-02)."""
    if target.is_dir():
        bundle = load_config_bundle(target)
        return check_bundle(bundle, store_root=store_root)

    data = _load_toml(target)
    kind = _classify_config_file(data, target)

    if kind == "task_profile":
        profile = _parse_task_profile(data, target)
        bundle = ConfigBundle(
            source_root=target.parent.resolve(),
            catalog=TaskCatalog({profile.name: profile}),
            models={},
            providers={},
        )
        return check_bundle(bundle)

    if kind == "model_candidates":
        models = _parse_model_candidates(data, target)
        providers = load_provider_endpoints(
            _resolve_lint_support_path(
                providers_path,
                (config_dir or target.parent) / "providers.toml",
                label="Provider",
            )
        )
        bundle = ConfigBundle(
            source_root=(config_dir or target.parent).resolve(),
            catalog=TaskCatalog({}),
            models=models,
            providers=providers,
        )
        return check_bundle(bundle)

    if kind == "providers":
        _parse_provider_endpoints(data, target)
        return []

    if kind == "run":
        run_config = _parse_run_config(data, target)
        bundle = load_support_bundle(
            target,
            config_dir=config_dir,
            task_profile_dir=task_profile_dir,
            model_candidates_path=model_candidates_path,
            providers_path=providers_path,
        )
        issues = check_bundle(
            bundle,
            store_root=store_root or run_config.store_root,
        )
        try:
            assemble_run_plan(
                run_config=run_config,
                catalog=bundle.catalog,
                models=bundle.models,
                providers=bundle.providers,
            )
        except ConfigurationError as exc:
            message = str(exc)
            if not any(it.message == message for it in issues):
                issues.append(
                    CheckIssue(
                        code="CFG-00107",
                        where=f"run:{target}",
                        message=message,
                    )
                )
        return issues

    if kind == "comparison":
        comparison = _parse_comparison_config(data, target)
        resolved_store_root = store_root or comparison.store_root
        if resolved_store_root is None:
            raise ConfigurationError(
                "Comparison 設定の検証には --store-root か comparison.store_root が必要"
            )
        return check_comparison(comparison, resolved_store_root)

    raise ConfigurationError(f"未対応の設定種別: {kind}")


# ---- 認証情報解決ルール (Phase 1 では未使用だが API を確保) ----------------


def resolve_env(var_name: str) -> str:
    """環境変数経由の認証情報解決 (CFG-00401).

    Phase 1 (Ollama) では未使用。将来 provider 拡張時の入口として残す。
    """
    val = os.environ.get(var_name)
    if val is None:
        raise ConfigurationError(
            f"認証情報の解決に必要な環境変数が未設定: {var_name}"
        )
    return val


# ---- 整合性検証 (CFG-00501..00506, TASK-00007-03) -------------------------


@dataclass(frozen=True)
class CheckIssue:
    """`check` (CLI-00105) で検出した問題 1 件 (FUN-00105 / FUN-00402).

    `code` は CFG-00501..00506 / SCR-00001 系の参照 ID を含む短い識別子。
    `where` は問題箇所 (Task Profile 名 / Model Candidate 名等) を示す。
    """

    code: str
    where: str
    message: str


def check_bundle(
    bundle: "ConfigBundle",
    store_root: Path | None = None,
) -> list[CheckIssue]:
    """設定一式の整合性検証 (CFG-00501..00505 / FUN-00105 / FUN-00402).

    - CFG-00501: TaskProfile/Case の必須項目は Loader 段階で例外化済みだが、
      期待出力欠落のように scorer が必須とする要件はここで検出する。
    - CFG-00502: Model Candidate の provider_kind が登録済み provider にあるか。
    - CFG-00503: 評価契約が参照する scorer が SCR- に存在するか。
    - CFG-00505: store_root が書込可能か (任意指定時のみ)。

    CFG-00504 (認証情報の環境変数解決) は v1 (Ollama) では認証要素が
    無いため、検出対象なし。CFG-00506 (Comparison) は別途 check_comparison
    で扱う。
    """
    # Local import to avoid circular dependency at module load time.
    from ..scoring import is_known_scorer

    issues: list[CheckIssue] = []

    # CFG-00502: provider 種別の登録確認
    for mc in bundle.models.values():
        if mc.provider_kind not in bundle.providers:
            issues.append(
                CheckIssue(
                    code="CFG-00502",
                    where=f"model_candidate:{mc.name}",
                    message=(
                        f"未知 provider 参照: provider_kind={mc.provider_kind}"
                        f" (登録済み: {sorted(bundle.providers)})"
                    ),
                )
            )

    # CFG-00503 + 期待出力欠落 (FUN-00105 観点)
    for tp in bundle.catalog.profiles.values():
        if not is_known_scorer(tp.scorer.name):
            issues.append(
                CheckIssue(
                    code="CFG-00503",
                    where=f"task_profile:{tp.name}",
                    message=(
                        f"未登録の scorer 参照: {tp.scorer.name}"
                    ),
                )
            )
        # 期待出力を必須とする scorer に対して expected_output が無い Case を検出
        if tp.scorer.name in (
            "exact_match",
            "normalized_match",
            "regex_match",
        ):
            for c in tp.cases:
                if c.expected_output is None:
                    issues.append(
                        CheckIssue(
                            code="CFG-00501",
                            where=f"task_profile:{tp.name}/case:{c.name}",
                            message=(
                                f"scorer={tp.scorer.name} は expected_output"
                                " を必須とする (FUN-00105)"
                            ),
                        )
                    )

    # CFG-00505: store_root が書込可能か
    if store_root is not None:
        ok, detail = _check_writable(store_root)
        if not ok:
            issues.append(
                CheckIssue(
                    code="CFG-00505",
                    where=f"store_root:{store_root}",
                    message=f"Result Store が書込不可: {detail}",
                )
            )

    return issues


def check_comparison(
    cfg: "ComparisonConfig",
    store_root: Path,
) -> list[CheckIssue]:
    """Comparison 設定検証 (CFG-00506).

    Run 識別子の実在性と TaskProfile セット一致を確認する。Run Comparator
    と同等の判定だが、`check` 用にエラーを集約する。
    """
    from ..storage import ResultStore  # 循環回避のため遅延 import

    issues: list[CheckIssue] = []
    store = ResultStore(store_root)

    profiles_per_run: dict[str, tuple[str, ...] | None] = {}
    for run_id in cfg.run_ids:
        try:
            meta = store.load_meta(run_id)
        except FileNotFoundError:
            issues.append(
                CheckIssue(
                    code="CFG-00506",
                    where=f"run_id:{run_id}",
                    message="Result Store に該当 Run が存在しない",
                )
            )
            profiles_per_run[run_id] = None
            continue
        tps = meta.get("task_profiles") or []
        profiles_per_run[run_id] = tuple(str(x) for x in tps)

    # TaskProfile セット一致 (DAT-00109)
    valid_sets = [v for v in profiles_per_run.values() if v is not None]
    if len(valid_sets) >= 2 and len({frozenset(v) for v in valid_sets}) > 1:
        issues.append(
            CheckIssue(
                code="CFG-00506",
                where="comparison",
                message=(
                    "比較対象 Run の TaskProfile セットが一致しない (DAT-00109)"
                    f" sets={profiles_per_run}"
                ),
            )
        )
    return issues


def _check_writable(path: Path) -> tuple[bool, str]:
    """ディレクトリ (または親) が書込可能かを副作用なしで確認する."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return False, str(exc)
    if not os.access(path, os.W_OK):
        return False, "書込権限なし"
    return True, "ok"

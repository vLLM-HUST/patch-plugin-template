# vLLM-HUST Patch Plugin Template

A GitHub template for a **default-off, single-mechanism runtime-patch plugin** for vLLM-HUST: a
`vllm.general_plugins` entry point that replaces one host function at runtime instead of
vendoring a modified copy of the host.

It complements [`extension-template`](https://github.com/vLLM-HUST/extension-template), which
scaffolds extension *shapes* and manifests. This template is about **how to patch a host function
safely and how to prove the patch is doing something**. The structure encodes mistakes made in
real extractions; see [docs/PITFALLS.md](docs/PITFALLS.md).

## Use it

1. Click **Use this template**, then clone your new repository.
2. Rename the placeholders in place:

   ```bash
   python tools/init_plugin.py \
     --name my-plugin \
     --maintainer-name "Your Name" \
     --maintainer-github your-login \
     --advisor-status unknown
   ```

   This rewrites `example-plugin` / `example_plugin` / `EXAMPLE_PLUGIN`, renames the package
   directory and removes the tool. Add `--dry-run` to preview, `--keep-tool` to keep it.
   Use `--advisor-status none` only when no advisor role applies. Use `unknown` when it has not
   been established; these are deliberately different states. If advisors apply, change the
   generated metadata status to `declared` and list each name and relationship; add a GitHub login
   when it is known.
3. Edit `src/<module>/plugin.py`: the four `TODO` constants and `_make_replacement`.
4. Replace `tests/fake_host.py` with a copy of the **verbatim** host code you replace, and keep the
   differential tests: they compare your replacement with that original on many random inputs.
5. `pip install -e ".[test]" && pytest`.
6. Fill in [docs/REPORT_TEMPLATE.md](docs/REPORT_TEMPLATE.md) with *measured* results, including
   what did not work.

## What is in the box

| Piece | Why |
| --- | --- |
| Default-off `register()`, `..._ENABLE`, `..._KILL_SWITCH` (kill switch wins) | A discovered plugin must do nothing until asked, and must be switchable off in production. |
| Source guard (`inspect.getsource`) | Refuse hosts that are unsupported or already optimised instead of patching speculatively. |
| `installed` and `runtime_effective` evidence events, with `pid` | "The patch is installed" and "the patch ran" are different facts; the pid shows *which process*. |
| `bootstrap.child_entry` | Gets the patch into processes the host starts with `spawn`. |
| Manifest `0.3-experimental` with an exclusive `resource_claims` entry | Lets the manager reject, before launch, two plugins that replace the same host function. Tests keep the claim, the entry points and `plugin.py` consistent. |
| Differential tests | The strongest evidence of behavioural equivalence for a runtime patch. |
| `tools/init_plugin.py` | GitHub templates do not substitute variables. |
| `docs/PITFALLS.md`, `docs/REPORT_TEMPLATE.md` | The lessons and a report skeleton that asks for advantages *and* limits. |
| `MOD_METADATA.json` | Canonical repository, direct responsibility, advisor state, lifecycle boundary, scope, and qualified evidence claims. |

## Repository metadata contract

`MOD_METADATA.json` is the human- and machine-readable summary of the MOD. Keep it aligned with
the README and the extension manifest. A repository copied from this template is not ready for
review until it has:

- the public `vLLM-HUST` canonical repository URL, with no private source-repository link or local path;
- at least one directly responsible maintainer;
- an explicit advisor state: `none`, `unknown`, or `declared` with a non-empty advisor list;
- `default_enabled: false`, an activation contract, and a rollback contract;
- a narrow mechanism scope and workload-qualified evidence;
- no performance claim unless its evidence index records the exact commits, dirty state, hardware,
  model, runtime, graph mode, command, repetitions, and evidence label.

Historical source commit hashes may be retained for provenance without presenting a private
organization as the canonical home. A microbenchmark, simulation, replay, or projected profile
must be labelled as such and must not be restated as an online end-to-end gain.

## Switches

| Variable | Effect |
| --- | --- |
| `VLLM_HUST_<NAME>_KILL_SWITCH=1` | Always wins. |
| `VLLM_HUST_<NAME>_ENABLE=1` | Required to install. Default off. `vllm-hust-ext extension enable` alone does **not** set it. |
| `VLLM_HUST_<NAME>_EVIDENCE=1` | Print `installed` and one `runtime_effective` event per process. |

## Manifest version

The manifest is `vllm-hust-extension-v0.3.json` (`0.3-experimental`), which the extension manager
looks for before `v0.2`. 0.3 keeps every 0.2 field and adds `resource_claims` and
`requires_extensions`; those two fields are illegal under 0.2. The 0.3 schema is under a
compatibility freeze and is not a stable v1 promise. See `docs/manifest-0.3-experimental.md` in
[`extension-manager`](https://github.com/vLLM-HUST/extension-manager).

The example claims `example-host.worker.compute` exclusively. **Change it together with the four
`TODO` constants in `plugin.py`**: a test fails if the claim does not name the function you replace.

## Not included, on purpose

No benchmark harness, no host-specific code, no claims. Whether a patch helps is established by
measuring it in the real serving path; see PITFALLS.

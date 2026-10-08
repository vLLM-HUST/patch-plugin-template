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
   python tools/init_plugin.py --name my-plugin
   ```

   This rewrites `example-plugin` / `example_plugin` / `EXAMPLE_PLUGIN`, renames the package
   directory and removes the tool. Add `--dry-run` to preview, `--keep-tool` to keep it.
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
| Differential tests | The strongest evidence of behavioural equivalence for a runtime patch. |
| `tools/init_plugin.py` | GitHub templates do not substitute variables. |
| `docs/PITFALLS.md`, `docs/REPORT_TEMPLATE.md` | The lessons and a report skeleton that asks for advantages *and* limits. |

## Switches

| Variable | Effect |
| --- | --- |
| `VLLM_HUST_<NAME>_KILL_SWITCH=1` | Always wins. |
| `VLLM_HUST_<NAME>_ENABLE=1` | Required to install. Default off. `vllm-hust-ext extension enable` alone does **not** set it. |
| `VLLM_HUST_<NAME>_EVIDENCE=1` | Print `installed` and one `runtime_effective` event per process. |

## Not included, on purpose

No benchmark harness, no host-specific code, no claims. Whether a patch helps is established by
measuring it in the real serving path; see PITFALLS.

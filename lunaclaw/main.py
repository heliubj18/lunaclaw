import asyncio

import click


@click.group(invoke_without_command=True)
@click.option("--model", "-m", default=None, help="Model name override")
@click.pass_context
def cli(ctx: click.Context, model: str | None) -> None:
    """Lunaclaw — a simple, powerful CLI agent assistant."""
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Start the interactive REPL."""
    from lunaclaw.interfaces.cli import run_repl

    model_override = ctx.obj.get("model") if ctx.obj else None
    asyncio.run(run_repl(model_override=model_override))


if __name__ == "__main__":
    cli()

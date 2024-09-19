# cloudestimate/cli.py

import click

@click.group()
def cli():
    """CloudEstimate CLI Tool"""
    pass

@cli.command()
def hello():
    """A simple test command"""
    click.echo("Hello from CloudEstimate!")

if __name__ == "__main__":
    cli()

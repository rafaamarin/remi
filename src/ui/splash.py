from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich.table import Table
from rich import box


ASCII_LOGO = """
[bold cyan on black]
╔╗ ╔╗╔╗╔╗   ╔╗╔════╗╔════╗╔════╗╔════╗╔╗╔═╗╔╗╔╗╔╗
║║ ║║║║║║   ║║║╔════╝║╔══╝║╔══╝║╔══╝║║║╔╗║║║║║║║║
║╚╗║║║║║║   ║║╠╝╔═╗  ║╚══╗╚═══╗╚═══╗║║║║║║║║╚╝║║║
╚╗║║║║║╚╗   ╔╝║║╔═╝  ║╔══╝║╔══╝║╔══╝║║║║║║║║╔╗║╚╝
 ╚═╝╚╝╚╝ ╚═══╝ ╚╝╚═╝  ╚╝   ╚╝   ╚╝   ╚═╝╚═╝╚╝╚╝
[/bold cyan on black]"""


SUBTITLE = "[bold magenta]Runtime Engine for Musical Instruments[/bold magenta]"


def get_splash_screen() -> Layout:
    tagline = Align(
        Text("[bold white]▓▓▓ POLYPHONIC SAMPLER ▓▓▓ TUI-FIRST ▓▓▓ ZERO COMPROMISE ▓▓▓[/bold white]", style="on black"),
        "center"
    )

    version = Align(Text("[dim]v0.1.0-alpha  •  Python 3.12+  •  Textual Engine[/dim]"), "center")

    tech_stack = Table(
        title="[bold cyan]◈ TECH STACK ◈[/bold cyan]",
        show_header=False,
        pad_edge=False,
        expand=False,
        border_style="cyan",
    )
    tech_stack.add_column(justify="left", style="cyan")
    tech_stack.add_row("[bold white]▸[/white] [green]Python 3.12+[/green]              [dim]GIL-aware runtime[/dim]")
    tech_stack.add_row("[bold white]▸[/white] [green]Textual (TUI)[/green]            [dim]GPU-accelerated terminal[/dim]")
    tech_stack.add_row("[bold white]▸[/white] [green]pygame-ce Mixer[/green]          [dim]Low-latency audio engine[/dim]")
    tech_stack.add_row("[bold white]▸[/white] [green]MIDI / Gamepad / Keyboard[/green] [dim]Universal input mapping[/dim]")

    controls = Table(
        title="[bold magenta]◈ CONTROLS ◈[/bold magenta]",
        show_header=False,
        pad_edge=False,
        expand=False,
        border_style="magenta",
        box=box.DOUBLE,
    )
    controls.add_column(justify="left", style="magenta")
    controls.add_row("[bold white]▸[/white] [bold yellow]Q W E R T Y[/bold yellow] [dim]Keyboard row 1[/dim]")
    controls.add_row("[bold white]▸[/white] [bold yellow]A S D F G H[/bold yellow] [dim]Keyboard row 2[/dim]")
    controls.add_row("[bold white]▸[/white] [bold yellow]Z X C V B N[/bold yellow] [dim]Keyboard row 3[/dim]")
    controls.add_row("[bold white]▸[/white] [bold yellow]1 2 3 4[/bold yellow]     [dim]Volume presets[/dim]")
    controls.add_row("[bold white]▸[/white] [bold yellow]TAB[/bold yellow]         [dim]Toggle mapping mode[/dim]")
    controls.add_row("[bold white]▸[/white] [bold yellow]ESC[/bold yellow]         [dim]Quit / dismiss[/dim]")

    features = Table(
        title="[bold yellow]◈ FEATURES ◈[/bold yellow]",
        show_header=False,
        pad_edge=False,
        expand=False,
        border_style="yellow",
        box=box.DOUBLE,
    )
    features.add_column(justify="left", style="yellow")
    features.add_row("[bold white]▸[/white] [bold green]Zero-latency[/bold green]   [dim]sample triggering[/dim]")
    features.add_row("[bold white]▸[/white] [bold green]Polyphonic[/bold green]    [dim]8-voice engine[/dim]")
    features.add_row("[bold white]▸[/white] [bold green]Dynamic mapping[/bold green] [dim]MIDI/gamepad learn[/dim]")
    features.add_row("[bold white]▸[/white] [bold green]RAM preload[/bold green]    [dim]no disk I/O on trigger[/dim]")
    features.add_row("[bold white]▸[/white] [bold green]Per-row volume[/bold green] [dim]4-channel mixer[/dim]")

    footer = Align(
        Text("[bold dim]▓▓▓ github.com/rafaamarin/remi ▓▓▓ press any key to start ▓▓▓[/bold dim]", style="on black"),
        "center"
    )

    header_content = Align(
        Text.from_markup(f"[bold cyan]{ASCII_LOGO}[/bold cyan]\n{SUBTITLE}"),
        "center"
    )

    body_content = Columns(
        [tech_stack, controls, features],
        equal=True,
        column_first=True,
    )

    layout = Layout()
    layout.split_column(
        Layout(name="header", ratio=2),
        Layout(name="body", ratio=4),
        Layout(name="footer", ratio=1),
    )

    from rich.console import Group
    layout["header"].update(Group(header_content, tagline, version))
    layout["body"].update(Align(body_content, "center"))
    layout["footer"].update(footer)

    return layout


if __name__ == "__main__":
    console = Console(force_terminal=True)
    console.print(get_splash_screen())
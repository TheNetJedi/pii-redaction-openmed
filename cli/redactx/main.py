"""RedactX CLI - Production-grade PII redaction from the command line."""

import sys
import os
from pathlib import Path
from typing import Optional, List
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel

# Add Core to path
current_file_path = Path(__file__).resolve()
# main.py -> redactx -> cli -> redac -> core
core_path = current_file_path.parents[3] / "core"
sys.path.append(str(core_path))

try:
    from redac_core.schemas import RedactionConfig, RedactionMethod, DeviceType
    from redac_core.services import get_redaction_service, get_document_handler
except ImportError as e:
    print(f"Error importing API services: {e}")
    sys.exit(1)

app = typer.Typer(
    name="redactx",
    help="🛡️ RedactX - Production-grade PII redaction powered by OpenMed",
    add_completion=False,
)
console = Console()


class Method(str, Enum):
    """Redaction methods wrapper for CLI."""
    mask = "mask"
    remove = "remove"
    replace = "replace"
    hash = "hash"
    shift_dates = "shift_dates"


# Default model (lightweight)
DEFAULT_MODEL = "openmed/OpenMed-PII-ClinicalE5-Small-33M-v1"


@app.command()
def redact(
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i", help="Input file to redact"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
    text: Optional[str] = typer.Option(
        None, "--text", "-t", help="Text to redact (alternative to file)"
    ),
    method: Method = typer.Option(
        Method.mask, "--method", "-m", help="Redaction method"
    ),
    confidence: float = typer.Option(
        0.6, "--confidence", "-c", min=0.0, max=1.0, help="Confidence threshold"
    ),
    model: str = typer.Option(
        DEFAULT_MODEL, "--model", help="Model to use for detection"
    ),
    show_entities: bool = typer.Option(
        False, "--show-entities", "-e", help="Show detected entities"
    ),
    stdin: bool = typer.Option(
        False, "--stdin", help="Read from stdin"
    ),
    entity_types: Optional[List[str]] = typer.Option(
        None, "--entity-type", "-E", help="Entity types to redact (repeatable)"
    ),
):
    """
    Redact PII from text or a file.

    PRO FEATURE: Reuses API logic to support PDF/DOCX layout preservation.
    """
    service = get_redaction_service()
    doc_handler = get_document_handler()
    
    # 1. Input Handling
    content: bytes | None = None
    input_text: str | None = None
    filename: str = "input.txt"

    if stdin:
        input_text = sys.stdin.read()
        filename = "stdin.txt"
    elif text:
        input_text = text
        filename = "cli_input.txt"
    elif input_file:
        if not input_file.exists():
            console.print(f"[red]Error:[/red] File not found: {input_file}")
            raise typer.Exit(1)
        
        filename = input_file.name
        if not doc_handler.is_supported(filename):
            console.print(f"[red]Error:[/red] Unsupported file type: {filename}")
            raise typer.Exit(1)
            
        # Read content
        content = input_file.read_bytes()
        # Extract Text
        try:
            input_text = doc_handler.extract_text(content, filename)
        except Exception as e:
            console.print(f"[red]Error reading file:[/red] {e}")
            raise typer.Exit(1)
    else:
        console.print("[red]Error:[/red] Provide --input, --text, or --stdin")
        raise typer.Exit(1)

    if not input_text or not input_text.strip():
        console.print("[yellow]Warning:[/yellow] Empty input")
        raise typer.Exit(0)

    # 2. Configuration
    config = RedactionConfig(
        model=model,
        confidence_threshold=confidence,
        method=RedactionMethod(method.value),
        entity_types=entity_types,
        use_smart_merging=True
    )

    # 3. Process
    with console.status(f"[cyan]Redacting with {model.split('/')[-1]}...[/cyan]"):
        try:
            result = service.redact_text(input_text, config)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # 4. Output Generation
    if output_file:
        # Use DocumentHandler to create smart output (PDF layout, DOCX, etc.)
        # We need original content for this. If text input, content is None.
        if content is None:
            content = input_text.encode('utf-8')
            
        try:
            redacted_content, _ = doc_handler.create_redacted_document(
                original_content=content,
                filename=filename,
                redacted_text=result.redacted_text,
                entities=result.entities,
                method=method.value
            )
            output_file.write_bytes(redacted_content)
            console.print(f"[green]✓[/green] Saved to {output_file}")
        except Exception as e:
             console.print(f"[red]Error saving output:[/red] {e}")
    else:
        console.print(Panel(result.redacted_text, title="Redacted Output", border_style="cyan"))

    # Summary
    console.print(f"\n[cyan]Entities found:[/cyan] {result.entity_count}")
    console.print(f"[cyan]Method:[/cyan] {method.value}")

    # Show entities if requested
    if show_entities and result.entities:
        table = Table(title="Detected Entities")
        table.add_column("Type", style="cyan")
        table.add_column("Text", style="white")
        table.add_column("Confidence", justify="right", style="green")

        for entity in sorted(result.entities, key=lambda e: e.start):
            table.add_row(entity.label, entity.text, f"{entity.confidence:.2%}")

        console.print(table)


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Directory with files to process"),
    output_dir: Path = typer.Argument(..., help="Output directory for redacted files"),
    method: Method = typer.Option(
        Method.mask, "--method", "-m", help="Redaction method"
    ),
    confidence: float = typer.Option(
        0.6, "--confidence", "-c", min=0.0, max=1.0, help="Confidence threshold"
    ),
    model: str = typer.Option(
        DEFAULT_MODEL, "--model", help="Model to use"
    ),
    pattern: str = typer.Option(
        "*.txt", "--pattern", "-p", help="File pattern to match"
    ),
    entity_types: Optional[List[str]] = typer.Option(
        None, "--entity-type", "-E", help="Entity types to redact (repeatable)"
    ),
):
    """Batch process multiple files."""
    service = get_redaction_service()
    doc_handler = get_document_handler()

    if not input_dir.exists():
        console.print(f"[red]Error:[/red] Directory not found: {input_dir}")
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Use pattern but allow all supported if reasonable? doc_handler supports different ones.
    # The user specifies pattern.
    files = list(input_dir.glob(pattern))
    if not files:
        console.print(f"[yellow]No files matching '{pattern}' in {input_dir}[/yellow]")
        raise typer.Exit(0)

    console.print(f"[cyan]Processing {len(files)} files...[/cyan]\n")

    total_entities = 0
    success = 0
    failed = 0

    config = RedactionConfig(
        model=model,
        confidence_threshold=confidence,
        method=RedactionMethod(method.value),
        entity_types=entity_types,
        use_smart_merging=True
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing", total=len(files))

        for file_path in files:
            progress.update(task, description=f"Processing {file_path.name}")
            
            if not doc_handler.is_supported(file_path.name):
                # Skip silently or warn? Silent for batch usually unless strict.
                progress.advance(task)
                continue

            try:
                content = file_path.read_bytes()
                text = doc_handler.extract_text(content, file_path.name)
                
                if not text.strip():
                    progress.advance(task)
                    continue

                result = service.redact_text(text, config)
                total_entities += result.entity_count

                # Create output
                redacted_content, new_filename = doc_handler.create_redacted_document(
                    original_content=content,
                    filename=file_path.name,
                    redacted_text=result.redacted_text,
                    entities=result.entities,
                    method=method.value
                )

                output_path = output_dir / new_filename
                output_path.write_bytes(redacted_content)

                success += 1
            except Exception as e:
                console.print(f"[red]Failed:[/red] {file_path.name}: {e}")
                failed += 1
                # Log to a file?

            progress.advance(task)

    # Summary
    console.print(f"\n[green]✓ Completed[/green]")
    console.print(f"  Success: {success}")
    console.print(f"  Failed: {failed}")
    console.print(f"  Total entities: {total_entities}")
    console.print(f"  Output: {output_dir}")


@app.command()
def extract(
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i", help="Input file"
    ),
    text: Optional[str] = typer.Option(
        None, "--text", "-t", help="Text to analyze"
    ),
    confidence: float = typer.Option(
        0.6, "--confidence", "-c", min=0.0, max=1.0, help="Confidence threshold"
    ),
    model: str = typer.Option(
        DEFAULT_MODEL, "--model", help="Model to use"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
):
    """Extract PII entities without redacting."""
    import json
    service = get_redaction_service()
    doc_handler = get_document_handler()

    input_text = ""
    if text:
        input_text = text
    elif input_file:
         try:
            input_text = doc_handler.extract_text(input_file.read_bytes(), input_file.name)
         except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    else:
        console.print("[red]Error:[/red] Provide --input or --text")
        raise typer.Exit(1)

    config = RedactionConfig(
        model=model,
        confidence_threshold=confidence,
    )

    with console.status(f"[cyan]Extracting entities...[/cyan]"):
        try:
            entities = service.extract_entities(input_text, config)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    if json_output:
        entities_json = [e.model_dump() for e in entities]
        print(json.dumps(entities_json, indent=2))
    else:
        if not entities:
            console.print("[yellow]No entities found[/yellow]")
        else:
            table = Table(title=f"Detected Entities ({len(entities)})")
            table.add_column("#", style="dim")
            table.add_column("Type", style="cyan")
            table.add_column("Text", style="white")
            table.add_column("Confidence", justify="right", style="green")
            table.add_column("Position", style="dim")

            for i, entity in enumerate(entities, 1):
                table.add_row(
                    str(i),
                    entity.label,
                    entity.text,
                    f"{entity.confidence:.1%}",
                    f"{entity.start}:{entity.end}",
                )

            console.print(table)

@app.command()
def models():
    """List available PII detection models."""
    # Hardcoded or fetch from Service if service had a list_models capability
    # For now, stick to hardcoded list or move list to core constant
    table = Table(title="Available Models")
    table.add_column("Model", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Notes")

    models_list = [
        ("OpenMed-PII-ClinicalE5-Small-33M-v1", "33M", "★ Default - Fastest"),
        ("OpenMed-PII-SuperClinical-Small-44M-v1", "44M", ""),
        ("OpenMed-PII-LiteClinical-Small-66M-v1", "66M", ""),
        ("OpenMed-PII-FastClinical-Small-82M-v1", "82M", "Fast inference"),
        ("OpenMed-PII-ClinicalE5-Base-109M-v1", "109M", ""),
        ("OpenMed-PII-BioClinicalModern-Base-149M-v1", "149M", ""),
        ("OpenMed-PII-SuperClinical-Base-184M-v1", "184M", ""),
        ("OpenMed-PII-SuperClinical-Large-434M-v1", "434M", "★ Best accuracy"),
        ("OpenMed-PII-QwenMed-XLarge-600M-v1", "600M", "Largest"),
    ]

    for name, size, notes in models_list:
        table.add_row(f"openmed/{name}", size, notes)

    console.print(table)


@app.command()
def methods():
    """List available redaction methods."""
    # Reuse enum from RedactionMethod if we want, or keep table
    table = Table(title="Redaction Methods")
    table.add_column("Method", style="cyan")
    table.add_column("Description")
    table.add_column("Example")

    methods_list = [
        ("mask", "Replace with [ENTITY_TYPE]", "John Doe → \[first_name] \[last_name]"),
        ("remove", "Completely remove", "John Doe → "),
        ("replace", "Synthetic data", "John Doe → Jane Smith"),
        ("hash", "Cryptographic hash", "John Doe → first_name_7e8c last_name_3013"),
        ("shift_dates", "Shift dates by N days", "01/15/2025 → 07/14/2025"),
    ]

    for method, desc, example in methods_list:
        table.add_row(method, desc, example)

    console.print(table)


@app.callback()
def main():
    """
    🛡️ RedactX - Production-grade PII redaction
    
    Powered by OpenMed's state-of-the-art PII detection models.
    HIPAA & GDPR compliant. Apache 2.0 licensed.
    """
    pass


if __name__ == "__main__":
    app()

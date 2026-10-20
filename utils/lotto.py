"""Persistent storage, PDF tickets, and result matching for Lotto pages."""

import csv
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

import msvcrt
from openpyxl import Workbook


REPORTS_ROOT = Path(__file__).resolve().parents[1]
LOTTO_CSV_PATH = REPORTS_ROOT / "csv" / "lotto_entries.csv"
LOTTO_PDF_DIRECTORY = Path(
    r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino"
    r"\Casino Marketing\CRM Reports\CM List\Lotto"
)
LOTTO_TIMEZONE = timezone(timedelta(hours=8), name="PHT")
LOTTO_HEADERS = [
    "submission_id",
    "player_number",
    "submitted_at",
    "number_1",
    "number_2",
    "number_3",
    "number_4",
    "number_5",
    "number_6",
    "pdf_file",
]


def normalize_player_number(value):
    player_number = str(value or "").strip().upper()
    if not player_number:
        raise ValueError("Player number is required.")
    if len(player_number) > 50:
        raise ValueError("Player number must be 50 characters or fewer.")
    if not re.fullmatch(r"[A-Z0-9-]+", player_number):
        raise ValueError("Player number may contain only letters, numbers, and hyphens.")
    return player_number


def normalize_numbers(values):
    try:
        numbers = sorted({int(value) for value in (values or [])})
    except (TypeError, ValueError):
        raise ValueError("Lotto numbers must be whole numbers from 1 to 49.")
    if len(numbers) != 6:
        raise ValueError("Select exactly 6 different numbers.")
    if numbers[0] < 1 or numbers[-1] > 49:
        raise ValueError("Lotto numbers must be from 1 to 49.")
    return numbers


def _pdf_escape(value):
    return (
        str(value)
        .encode("ascii", "replace")
        .decode("ascii")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def build_ticket_pdf(player_number, submitted_at, numbers):
    """Build a dependency-free, one-page PDF ticket."""
    lines = [
        (24, 72, 740, "LOTTO ENTRY"),
        (13, 72, 695, "Player Number: {}".format(player_number)),
        (13, 72, 670, "Submitted At: {}".format(submitted_at)),
        (16, 72, 620, "Numbers: {}".format("  -  ".join(map(str, numbers)))),
    ]
    commands = ["BT"]
    for size, x, y, text in lines:
        commands.extend(
            [
                "/F1 {} Tf".format(size),
                "{} {} Td".format(x, y),
                "({}) Tj".format(_pdf_escape(text)),
                "{} {} Td".format(-x, -y),
            ]
        )
    commands.append("ET")
    stream = ("\n".join(commands) + "\n").encode("ascii")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream
        + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend("{} 0 obj\n".format(number).encode("ascii"))
        document.extend(obj)
        document.extend(b"\nendobj\n")

    xref_offset = len(document)
    document.extend("xref\n0 {}\n".format(len(objects) + 1).encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend("{:010d} 00000 n \n".format(offset).encode("ascii"))
    document.extend(
        (
            "trailer\n<< /Size {} /Root 1 0 R >>\nstartxref\n{}\n%%EOF\n".format(
                len(objects) + 1,
                xref_offset,
            )
        ).encode("ascii")
    )
    return bytes(document)


@contextmanager
def _exclusive_file_lock(lock_path, timeout=10.0):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"0")
            lock_file.flush()

        deadline = time.monotonic() + timeout
        while True:
            try:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Timed out waiting for Lotto storage lock.")
                time.sleep(0.05)
        try:
            yield
        finally:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


class LottoStore(object):
    def __init__(self, csv_path=LOTTO_CSV_PATH, pdf_directory=LOTTO_PDF_DIRECTORY):
        self.csv_path = Path(csv_path)
        self.pdf_directory = Path(pdf_directory)
        self.lock_path = self.csv_path.with_suffix(self.csv_path.suffix + ".lock")

    def _read_unlocked(self):
        if not self.csv_path.exists():
            return []
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != LOTTO_HEADERS:
                raise ValueError("Unexpected Lotto CSV columns: {}".format(reader.fieldnames))
            return list(reader)

    def read(self):
        with _exclusive_file_lock(self.lock_path):
            return self._read_unlocked()

    def submit(self, submission_id, player_number, numbers):
        submission_id = str(submission_id or "").strip()
        if not submission_id:
            raise ValueError("Submission ID is required.")
        player_number = normalize_player_number(player_number)
        numbers = normalize_numbers(numbers)

        with _exclusive_file_lock(self.lock_path):
            existing = self._read_unlocked()
            duplicate = next(
                (
                    record
                    for record in existing
                    if record.get("submission_id") == submission_id
                ),
                None,
            )
            if duplicate:
                return duplicate, False

            submitted_at = datetime.now(LOTTO_TIMEZONE).isoformat(timespec="seconds")
            safe_player = re.sub(r"[^A-Z0-9-]+", "_", player_number)
            timestamp = datetime.now(LOTTO_TIMEZONE).strftime("%Y%m%d_%H%M%S_%f")
            pdf_filename = "Lotto_{}_{}.pdf".format(safe_player, timestamp)
            pdf_path = self.pdf_directory / pdf_filename
            temp_pdf_path = pdf_path.with_suffix(".pdf.tmp")

            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            self.pdf_directory.mkdir(parents=True, exist_ok=True)
            pdf_bytes = build_ticket_pdf(player_number, submitted_at, numbers)
            try:
                with temp_pdf_path.open("wb") as file:
                    file.write(pdf_bytes)
                    file.flush()
                    os.fsync(file.fileno())
                temp_pdf_path.replace(pdf_path)

                record = {
                    "submission_id": submission_id,
                    "player_number": player_number,
                    "submitted_at": submitted_at,
                    **{
                        "number_{}".format(index): number
                        for index, number in enumerate(numbers, start=1)
                    },
                    "pdf_file": str(pdf_path),
                }
                write_header = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
                with self.csv_path.open("a", encoding="utf-8-sig", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=LOTTO_HEADERS)
                    if write_header:
                        writer.writeheader()
                    writer.writerow(record)
                    file.flush()
                    os.fsync(file.fileno())
                return {key: str(value) for key, value in record.items()}, True
            except Exception:
                for candidate in (temp_pdf_path, pdf_path):
                    try:
                        if candidate.exists():
                            candidate.unlink()
                    except OSError:
                        pass
                raise


def match_entries(records, winning_numbers):
    winning = set(normalize_numbers(winning_numbers))
    results = []
    for record in records:
        selected = {
            int(record["number_{}".format(index)])
            for index in range(1, 7)
        }
        matches = len(selected.intersection(winning))
        results.append(
            {
                "player_number": record.get("player_number", ""),
                "submitted_at": record.get("submitted_at", ""),
                "selected_numbers": ", ".join(map(str, sorted(selected))),
                "matches": matches,
            }
        )
    return sorted(
        results,
        key=lambda record: (-record["matches"], record["player_number"]),
    )


def build_results_workbook(results, winning_numbers):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Lotto Results"
    sheet.append(["Winning Numbers", ", ".join(map(str, normalize_numbers(winning_numbers)))])
    sheet.append([])
    sheet.append(["Player Number", "Matches"])
    for result in results:
        sheet.append([result["player_number"], int(result["matches"])])
    sheet.column_dimensions["A"].width = 24
    sheet.column_dimensions["B"].width = 12

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


__all__ = [
    "LOTTO_CSV_PATH",
    "LOTTO_PDF_DIRECTORY",
    "LottoStore",
    "build_results_workbook",
    "build_ticket_pdf",
    "match_entries",
    "normalize_numbers",
    "normalize_player_number",
]

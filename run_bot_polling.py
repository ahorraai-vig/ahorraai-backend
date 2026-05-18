from __future__ import annotations

import asyncio

from ahorraai_vigo.dev.polling import run_polling


if __name__ == "__main__":
    asyncio.run(run_polling())

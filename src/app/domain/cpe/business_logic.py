from phantom_communicator.communicator_asyncio import Communicator

from app.lib import worker

__all__ = ["communicate_with_cpe", "readout_cpe"]


async def communicate_with_cpe(ctx, *, ip, os):
    communicator = Communicator.factory(host=ip, os=os)
    async with communicator as conn:
        await conn.send_commands(
            [
                "copy run start\n",
                "show run",
                "show ip int brief",
            ]
        )
        await conn.get_version()
        await conn.get_startup_config()
        await conn.get_boot_files()
        await conn.genie_parse_output()  # for this one we will later make an override.
        # because pyats is very slow upgrading to higher python versions. and i want to keep the project up to date because of the speed improvements in python itself

        await conn.send_interactive_command(
            [("copy run start", "Destination filename [startup-config]?", False), ("\n", "[OK]", False)]
        )


async def readout_cpe(ip: str, os: str):
    await worker.queues["background-tasks"].enqueue("communicate_with_cpe", ip=ip, os=os, timeout=60)

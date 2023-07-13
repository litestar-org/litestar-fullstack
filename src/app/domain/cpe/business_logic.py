from phantom_communicator.communicator_asyncio import Communicator

__all__ = ["readout_cpe"]


async def readout_cpe(ip: str, os: str):
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
        await conn.genie_parse_output()

        await conn.send_interactive_command(
            [("copy run start", "Destination filename [startup-config]?", False), ("\n", "[OK]", False)]
        )

        get_running_config = await conn.save_device_config(ip)
        print(get_running_config, ip)

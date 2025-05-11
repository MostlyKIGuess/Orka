import argparse
import asyncio
import logging
import os
import signal
import sys
import importlib.util  # For running original main in standalone
from typing import Optional
import threading

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from client_config import ClientConfig
    from network_logic import NetworkLogic
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import client modules. sys.path={sys.path}. Error: {e}", file=sys.stderr)
    sys.exit(1)

# Configure basic logging for the client
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("client.main")

network_logic_instance: Optional[NetworkLogic] = None
main_task: Optional[asyncio.Task] = None

async def graceful_shutdown(sig: Optional[signal.Signals] = None):
    global main_task
    if sig:
        logger.info(f"Received exit signal {sig.name}. Shutting down client...")
    else:
        logger.info("Initiating client shutdown...")

    if network_logic_instance:
        await network_logic_instance.stop(f"Shutdown by {sig.name if sig else 'program'}")

    if main_task and not main_task.done():
        main_task.cancel()
        try:
            await main_task
        except asyncio.CancelledError:
            logger.info("Main client task cancelled.")

    logger.info("Client shutdown sequence complete.")

def run_original_app_standalone(cfg: ClientConfig):
    logger.info("Running original app in standalone mode.")
    original_main_py = os.path.join(cfg.ORIGINAL_APP_SRC_PATH, 'main.py')
    if not os.path.exists(original_main_py):
        logger.error(f"main.py not found at {original_main_py}")
        print(f"ERROR: '{original_main_py}' missing")
        return

    # try to setup original logging via utils.py
    try:
        utils_py = os.path.join(cfg.ORIGINAL_APP_SRC_PATH, 'utils.py')
        if os.path.exists(utils_py):
            spec_u = importlib.util.spec_from_file_location("orig_utils", utils_py)
            if spec_u and spec_u.loader:
                mod_u = importlib.util.module_from_spec(spec_u)
                sys.modules['orig_utils'] = mod_u
                spec_u.loader.exec_module(mod_u)
                if hasattr(mod_u, 'setup_logging'):
                    mod_u.setup_logging()
    except Exception as e:
        logger.warning(f"Could not init original app logging: {e}")

    # import and call original main()
    spec_m = importlib.util.spec_from_file_location("orig_main", original_main_py)
    if spec_m and spec_m.loader:
        mod_m = importlib.util.module_from_spec(spec_m)
        if cfg.ORIGINAL_APP_SRC_PATH not in sys.path:
            sys.path.insert(0, cfg.ORIGINAL_APP_SRC_PATH)
        sys.modules['orig_main'] = mod_m
        spec_m.loader.exec_module(mod_m)
        if hasattr(mod_m, 'main'):
            mod_m.main()
        else:
            logger.error("original main.py has no main()")
    else:
        logger.error(f"Cannot load spec for {original_main_py}")

async def client_main_loop(args):
    global network_logic_instance, main_task
    main_task = asyncio.current_task()
    cfg = ClientConfig()
    if args.server_url:
        cfg.SERVER_URL = args.server_url
    if not cfg.SERVER_URL and not args.standalone:
        logger.error("Server URL required (--server or env var).")
        return

    if args.standalone:
        run_original_app_standalone(cfg)
        return

    network_logic_instance = NetworkLogic(cfg, shutdown_callback=graceful_shutdown)
    loop = asyncio.get_event_loop()
    for s in (signal.SIGINT, signal.SIGTERM, getattr(signal, 'SIGHUP', None)):
        if s:
            try:
                loop.add_signal_handler(s, lambda s=s: asyncio.create_task(graceful_shutdown(s)))
            except Exception:
                pass

    logger.info(f"Connecting to {cfg.SERVER_URL} as {cfg.CLIENT_NAME}...")
    await network_logic_instance.connect_and_run()
    logger.info("Client main loop ended.")

def unified_loop(cfg: ClientConfig):
    """
    Single REPL: free-text sends speak_text, 'photo' triggers capture_image.
    """
    net = NetworkLogic(cfg, shutdown_callback=None)
    # connect once (assumes connect_and_run can take a startup-only flag)
    asyncio.run(net.connect_and_run(startup_only=True))

    print("\n--- Interactive Chat + Photo Mode ---")
    print("Type text to chat, 'photo' to snap+roast, 'quit' to exit.")
    while True:
        cmd = input("> ").strip()
        if not cmd:
            continue
        if cmd.lower() in ("quit", "exit"):
            print("Goodbye!")
            asyncio.run(net.stop("User exit"))
            break
        if cmd.lower() in ("photo", "p", "image"):
            resp = asyncio.run(net.send_command("capture_image", {}))
            print("capture_image response:", resp)
            continue
        # treat as TTS chat
        resp = asyncio.run(net.send_command("speak_text", {"text": cmd}))
        print("speak_text response:", resp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client Application")
    parser.add_argument(
        "--server", dest="server_url", type=str, default=None,
        help="WebSocket URL (e.g. ws://localhost:8765)"
    )
    parser.add_argument(
        "--standalone", action="store_true",
        help="Run original app in standalone mode"
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Run unified chat+photo REPL"
    )
    parser.add_argument(
        "--both", action="store_true",
        help="Connect to server AND run original app together"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    cfg = ClientConfig()
    if args.server_url:
        cfg.SERVER_URL = args.server_url

    # --both: connect to server (startup only) then run original CLI
    if args.both:
        net = NetworkLogic(cfg, shutdown_callback=None)

        # 1) start the *full* connect_and_run() in a background thread
        def _run_network():
            asyncio.run(net.connect_and_run())   # no startup_only here
        t = threading.Thread(target=_run_network, daemon=True)
        t.start()

        # 2) now launch the original standalone app (blocks here)
        run_original_app_standalone(cfg)

        # 3) once the standalone app exits, cleanly shut down the WS
        asyncio.run(net.stop("Original app exited"))
        t.join()
        sys.exit(0)

    if args.interactive:
        unified_loop(cfg)
    else:
        try:
            # standalone only
            if args.standalone:
                # first connect to server (handshake only)
                net = NetworkLogic(cfg, shutdown_callback=None)
                asyncio.run(net.connect_and_run(startup_only=True))
                # then run original app
                run_original_app_standalone(cfg)
            else:
                asyncio.run(client_main_loop(args))
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except asyncio.CancelledError:
            logger.info("Cancelled")
        except Exception as e:
            logger.exception(f"Fatal exception: {e}")

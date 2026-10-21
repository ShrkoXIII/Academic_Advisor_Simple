"""Run the private pilot server or one reproducible batch."""
import argparse
import json

from .adapter import PILOT_ROOT, read_students


def main():
    parser = argparse.ArgumentParser(description="Local-only Academic Advisor Pilot 20251")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--run-all", action="store_true", help="Run all saved primary students and exit")
    parser.add_argument("--credits", type=float, default=18)
    parser.add_argument("--max-plans", type=int, default=200)
    args = parser.parse_args()
    if args.run_all:
        from .runner import ComparisonRunner
        runner = ComparisonRunner(PILOT_ROOT)
        try:
            result = runner.run_sync([s["sample_id"] for s in read_students()], target_credits=args.credits, max_plans=args.max_plans)
            print(json.dumps(result))
            if result["status"] == "failed":
                raise SystemExit(1)
        finally:
            runner.executor.shutdown(wait=True)
    else:
        import uvicorn
        from .app import create_app
        uvicorn.run(create_app(), host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()

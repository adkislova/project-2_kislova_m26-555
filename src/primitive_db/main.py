#!/usr/bin/env python3
import primitive_db.engine


def main():
    primitive_db.engine.print_help()
    primitive_db.engine.run()


if __name__ == "__main__":
    main()

from subprocess import run


def main() -> None:
    run(
        [
            "ssh",
            "oc",
            "cd srv/website; git pull; systemctl restart --user website",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()

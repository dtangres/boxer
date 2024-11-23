from boxer.gameInfo import ingredientsNormalizedToProper
from boxer.stringManip import normalizeName


def read_reagents(filename):
    """
    Reads reagents from a save file and returns them as a list of dictionaries.
    """
    output = {}
    print("Collecting data...")
    with open(filename, "rb") as infile:
        # Skip preamble
        infile.read(0x1F)
        reagentsToCount = int.from_bytes(infile.read(0x1))
        infile.read(0x4)
        reagentCounter = 0
        # Read in inventory data
        for r in range(reagentsToCount):
            wideCheck = infile.read(0x3)
            special = wideCheck == b"\xff\xff\xff"
            name = b""
            buff = b""
            while (special and buff != b"\x00\x00") or (
                not (special) and buff != b"\x00"
            ):
                name += buff
                buff = infile.read(0x2) if special else infile.read(0x1)
            if special:
                name = name.decode("utf-16")
            else:
                name = name.decode("utf-8")
            # read unknown0
            infile.read(0xE0)

            unknown0 = infile.read(0x1)
            infile.read(0x3)

            # read unknown1
            unknown1 = []
            for i in range(int.from_bytes(unknown0) + 2):
                buff = infile.read(0x1)
                unknown1.append(int.from_bytes(buff))

            infile.read(0x3)
            magiminsEntries = unknown1[-1]

            # read magimins
            magimins = {}
            for i in range(magiminsEntries):
                magiminType = "ABCDE"[int.from_bytes(infile.read(0x1))]
                magiminAmount = int.from_bytes(infile.read(0x1))
                magimins[magiminType] = magiminAmount
                infile.read(0x3)
            infile.read(0x9)
            quantity = int.from_bytes(infile.read(0x1))
            infile.read(0x3)
            unknown3 = int.from_bytes(infile.read(0x1))
            reagentCounter += 1

            # display ingredient, quantity
            # print(name, unknown2, unknown0, unknown1, unknown3, sep=",")
            output[name] = quantity
    result = {
        ingredientsNormalizedToProper[normalizeName(k)]: v for k, v in output.items()
    }
    return result

from enum import Enum
import pandas as pd
from pulp import (
    LpVariable,
    LpProblem,
    LpMaximize,
    LpMinimize,
    LpConstraint,
    LpConstraintLE,
    LpConstraintEQ,
    LpConstraintGE,
    LpStatus,
    value,
    getSolver,
    lpSum,
    PULP_CBC_CMD,
    listSolvers,
)

from gameInfo import (
    PotionIngredient,
    PotionTier,
    PotionType,
    potionRatios,
    starRequirements,
    cauldronProperties,
    Cauldron,
    SensoryQuality,
    ingredientData,
    PotionStability,
    potionBasePrices,
)

M = 3000
eenyminy = 0.0001


class PotionOptimizationObjective(Enum):
    BEST_FOR_GIVEN_TYPE = 1
    CHEAPEST_FOR_GIVEN_STARS = 2
    MOST_PROFITABLE_BATCH = 3


class BoxerException(Exception):
    pass


def testOrComplain(condition, message):
    try:
        assert condition
    except AssertionError:
        raise BoxerException(message)


def assertProblemIsComplete(
    ingredientInventory=None,
    cauldron=None,
    potionType=None,
    objective=None,
    starLevel=None,
    tier=None,
):
    testOrComplain(
        ingredientInventory is not None,
        "You have to specify ingredients with which to brew!",
    )
    testOrComplain(cauldron is not None, "You have to specify a cauldron to brew in!")
    testOrComplain(potionType is not None, "You have to specify a potion type to brew!")
    testOrComplain(
        potionType in PotionType,
        "You have to specify a valid potion type to brew!",
    )
    testOrComplain(
        objective is not None, "You have to specify an optimization objective!"
    )
    testOrComplain(
        objective in PotionOptimizationObjective,
        "You have to specify a valid optimization objective!",
    )
    if objective == PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE:
        testOrComplain(
            starLevel is None and tier is None,
            "You can't specify star level or tier for this objective!",
        )
    elif objective == PotionOptimizationObjective.CHEAPEST_FOR_GIVEN_STARS:
        testOrComplain(
            starLevel is not None or tier is not None,
            "You need to specify at least one of star level or tier!",
        )


def getBestPotion(
    ingredientInventory=None,
    cauldron=None,
    potionType=None,
    objective=PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE,
    stability=PotionStability.UNSTABLE,
    starLevel=None,
):
    # Establish common vars
    workingCauldron = cauldronProperties.loc[cauldron]
    magiminThresholds = starRequirements.loc["magimins"]

    # Declare maximization problem
    prob = None
    if objective == PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE:
        prob = LpProblem("Best Potion", LpMaximize)
    elif objective == PotionOptimizationObjective.CHEAPEST_FOR_GIVEN_STARS:
        prob = LpProblem("Cheapest Potion", LpMinimize)
    elif objective == PotionOptimizationObjective.MOST_PROFITABLE_BATCH:
        prob = LpProblem("Most Profitable Batch", LpMaximize)

    # Convert inventory dataframe to LpVariables
    inventoryVariables = {
        index: LpVariable(
            f"Ingredient_{index.name}",
            cat="Integer",
            lowBound=0,
            upBound=workingCauldron["maxIngredients"]
            if objective == PotionOptimizationObjective.MOST_PROFITABLE_BATCH
            else min(series["quantity"], workingCauldron["maxIngredients"]),
        )
        for index, series in ingredientInventory.iterrows()
    }

    ingredientQuantity = lpSum(inventoryVariables.values())

    # Define magimin counts for each type based on ingredients used
    magiminAmount_A = lpSum(
        ingredientData[k]["A"] * v for k, v in inventoryVariables.items()
    )
    magiminAmount_B = lpSum(
        ingredientData[k]["B"] * v for k, v in inventoryVariables.items()
    )
    magiminAmount_C = lpSum(
        ingredientData[k]["C"] * v for k, v in inventoryVariables.items()
    )
    magiminAmount_D = lpSum(
        ingredientData[k]["D"] * v for k, v in inventoryVariables.items()
    )
    magiminAmount_E = lpSum(
        ingredientData[k]["E"] * v for k, v in inventoryVariables.items()
    )

    # Define total magimins affine expression
    totalMagimins = lpSum(
        [
            magiminAmount_A,
            magiminAmount_B,
            magiminAmount_C,
            magiminAmount_D,
            magiminAmount_E,
        ]
    )

    # Define a few constants
    ratioSum = potionRatios.loc[potionType].sum()

    # Normalize potion ratios to sum to 1
    magiminRatioA = potionRatios.loc[potionType]["A"] / ratioSum
    magiminRatioB = potionRatios.loc[potionType]["B"] / ratioSum
    magiminRatioC = potionRatios.loc[potionType]["C"] / ratioSum
    magiminRatioD = potionRatios.loc[potionType]["D"] / ratioSum
    magiminRatioE = potionRatios.loc[potionType]["E"] / ratioSum

    magiminOff_A = LpVariable(
        "magiminDeviance_A",
        lowBound=0,
        upBound=workingCauldron["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_A >= totalMagimins * magiminRatioA - magiminAmount_A
    prob += magiminOff_A >= magiminAmount_A - totalMagimins * magiminRatioA

    magiminOff_B = LpVariable(
        "magiminDeviance_B",
        lowBound=0,
        upBound=workingCauldron["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_B >= totalMagimins * magiminRatioB - magiminAmount_B
    prob += magiminOff_B >= magiminAmount_B - totalMagimins * magiminRatioB

    magiminOff_C = LpVariable(
        "magiminDeviance_C",
        lowBound=0,
        upBound=workingCauldron["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_C >= totalMagimins * magiminRatioC - magiminAmount_C
    prob += magiminOff_C >= magiminAmount_C - totalMagimins * magiminRatioC

    magiminOff_D = LpVariable(
        "magiminDeviance_D",
        lowBound=0,
        upBound=workingCauldron["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_D >= totalMagimins * magiminRatioD - magiminAmount_D
    prob += magiminOff_D >= magiminAmount_D - totalMagimins * magiminRatioD

    magiminOff_E = LpVariable(
        "magiminDeviance_E",
        lowBound=0,
        upBound=workingCauldron["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_E >= totalMagimins * magiminRatioE - magiminAmount_E
    prob += magiminOff_E >= magiminAmount_E - totalMagimins * magiminRatioE

    totalDeviance = lpSum(
        [magiminOff_A, magiminOff_B, magiminOff_C, magiminOff_D, magiminOff_E]
    )

    prob += totalDeviance <= totalMagimins / 2

    # Convert magimin count to star count
    magiminStarVariables = {
        f"magiminStar_{i}": LpVariable(f"magiminStar_{i}", cat="Binary")
        for i in range(len(magiminThresholds) - 1)
    }
    magiminStarDummyArray_0 = {
        f"magiminStar_{i}_dummy0": LpVariable(f"magiminStar_{i}_dummy0", cat="Binary")
        for i in range(len(magiminThresholds) - 1)
    }
    magiminStarDummyArray_1 = {
        f"magiminStar_{i}_dummy1": LpVariable(f"magiminStar_{i}_dummy1", cat="Binary")
        for i in range(len(magiminThresholds) - 1)
    }
    for v, t_0, t_1, a, b in zip(
        magiminStarVariables.values(),
        magiminStarDummyArray_0.values(),
        magiminStarDummyArray_1.values(),
        magiminThresholds.values,
        magiminThresholds.values[1:],
    ):
        prob += a * v <= totalMagimins
        prob += totalMagimins <= (b - 1) * v + M * (1 - v)
        prob += totalMagimins - a <= M * t_0
        prob += (b - 1) - totalMagimins <= M * t_1
        prob += v >= t_0 + t_1 - 1

    # Convert stability to star bonus
    perfectStarBonus = LpVariable("perfectStarBonus", cat="Binary")
    veryStableStarBonus = LpVariable("veryStableStarBonus", cat="Binary")
    veryStableStarDummy0 = LpVariable("veryStableStarDummy0", cat="Binary")
    veryStableStarDummy1 = LpVariable("veryStableStarDummy1", cat="Binary")
    stableStarBonus = LpVariable("stableStarBonus", cat="Binary")
    stableStarDummy0 = LpVariable("stableStarDummy0", cat="Binary")
    stableStarDummy1 = LpVariable("stableStarDummy1", cat="Binary")
    unstableStarPenalty = LpVariable("unstableStarPenalty", cat="Binary")

    # Perfect potions require a perfect balance
    prob += totalDeviance <= M * (1 - perfectStarBonus)
    prob += (1 - perfectStarBonus) <= M * totalDeviance

    # Very stable potions require no more than 10% deviance
    lowerBound_veryStable = eenyminy
    upperBound_veryStable = 0.1
    prob += lowerBound_veryStable * veryStableStarBonus <= totalDeviance
    prob += totalDeviance <= upperBound_veryStable * totalMagimins + M * (
        1 - veryStableStarBonus
    )
    prob += totalDeviance - lowerBound_veryStable <= M * veryStableStarDummy0
    prob += upperBound_veryStable - totalDeviance <= M * veryStableStarDummy1
    prob += veryStableStarBonus >= veryStableStarDummy0 + veryStableStarDummy1 - 1

    # Stable potions require between 10% and 33% deviance exclusive
    lowerBound_stable = 0.1 + eenyminy
    upperBound_stable = (1 / 3) - eenyminy
    prob += lowerBound_stable * stableStarBonus <= totalDeviance
    prob += totalDeviance <= upperBound_stable * totalMagimins + M * (
        1 - stableStarBonus
    )
    prob += totalDeviance - lowerBound_stable <= M * stableStarDummy0
    prob += upperBound_stable - totalDeviance <= M * stableStarDummy1
    prob += stableStarBonus >= stableStarDummy0 + stableStarDummy1 - 1

    # Anything else is, of course, unstable
    prob += (
        perfectStarBonus + veryStableStarBonus + stableStarBonus + unstableStarPenalty
        == 1
    )
    # Stability may not be less than 50%
    prob += totalDeviance <= totalMagimins * 0.5

    # Specify cauldron constraints
    prob += totalMagimins <= workingCauldron["maxMagimins"]
    prob += ingredientQuantity <= workingCauldron["maxIngredients"]
    prob += 1 <= ingredientQuantity

    starsFromStability = (
        2 * perfectStarBonus
        + 1 * veryStableStarBonus
        + 0 * stableStarBonus
        - 1 * unstableStarPenalty
    )
    starsFromMagimins = lpSum(
        [index * i for index, i in enumerate(magiminStarVariables.values())]
    )
    totalStars = starsFromMagimins + starsFromStability
    prob += sum(magiminStarVariables.values()) == 1

    basePotionPrice = lpSum(
        [
            v * p
            for v, p in zip(magiminStarVariables.values(), potionBasePrices[potionType])
        ]
    )

    ingredientCosts = lpSum(
        [
            ingredientData[i]["basePrice"] * inventoryVariables[i]
            for i in inventoryVariables.keys()
        ]
    )

    # Fiddle with the objective a bit
    if objective == PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE:
        prob += totalStars  # + ingredientQuantity / 2
    elif objective == PotionOptimizationObjective.CHEAPEST_FOR_GIVEN_STARS:
        prob += starsFromMagimins + starsFromStability >= starLevel
        prob += ingredientCosts  # - basePotionPrice
    elif objective == PotionOptimizationObjective.MOST_PROFITABLE_BATCH:
        prob += ingredientQuantity == workingCauldron["maxIngredients"]
        prob += perfectStarBonus == 1
        prob += basePotionPrice * workingCauldron["maxIngredients"] - ingredientCosts
    prob.writeMPS("Potion.txt")
    listSolvers(onlyAvailable=True)
    prob.solve()
    if LpStatus[prob.status] == "Optimal":
        print(prob.variables())

        for i, j in inventoryVariables.items():
            ingredientAmt = int(j.value())
            if ingredientAmt:
                print(f"  {ingredientAmt}x {i}")

        for i in "ABCDE":
            magiminAmt = eval(f"int(magiminAmount_{i}.value())")
            print(f"    {i}:", [" ", magiminAmt][magiminAmt > 0])

        print(f"{magiminOff_A.value()=}")
        print(f"{magiminOff_B.value()=}")
        print(f"{magiminOff_C.value()=}")
        print(f"{magiminOff_D.value()=}")
        print(f"{magiminOff_E.value()=}")
        print()
        # print(f"{stabilityPerfect.value()=}")
        # print(f"{stabilityVeryStable.value()=}")
        # print(f"{stabilityStable.value()=}")
        print()
        print(f"{totalMagimins.value()=}")
        # print(f"{totalMagimins*0.1}")
        if totalMagimins.value():
            print(
                f"{totalDeviance.value()=}",
                f"({100 - round(totalDeviance.value() / totalMagimins.value()*100,2)}% stable)",
            )
        for index, i in enumerate(magiminStarVariables.values()):
            if i.value():
                print(f"Potion stars from magimins: {index*i.value()}")
        for i, j in zip(
            [
                perfectStarBonus,
                veryStableStarBonus,
                stableStarBonus,
                unstableStarPenalty,
            ],
            ["perfect", "very stable", "stable", "unstable"],
        ):
            if i.value():
                print(f"Potion stability: {j}")
        # for index, i in enumerate(totalStarsVariables.values()):
        #     if i.value():
        #         print(f"Total potion stars: {index*i.value()}")
        print(f"{ingredientQuantity.value()=}")
        # print("Base star value:", sum(i.value() for i in potionStarVariables))
        # print(f"{[i.value() for i in magiminStars]=}", sum(i.value() for i in magiminStars))
        # print([i.value() for i in potionStarConstraints[:6]])
        # print(sum((i + 1) * j.value() for i, j in enumerate(magiminStars)))
        print(f"{basePotionPrice.value()=}")
        print(f"Base batch price: {basePotionPrice.value()*ingredientQuantity.value()}")
        print(f"{ingredientCosts.value()=}")
        print(
            f"Base net profit: {basePotionPrice.value()*ingredientQuantity.value()-ingredientCosts.value()}"
        )
        print(
            f"Actual batch price: {potionBasePrices[potionType][totalStars.value()]*ingredientQuantity.value()}"
        )
        print(
            f"Actual net profit: {potionBasePrices[potionType][totalStars.value()]*ingredientQuantity.value()-ingredientCosts.value()}"
        )
        return prob
    else:
        print("No solution found. Please recheck your inputs.")


def getOptimumPotionRecipe(
    ingredientInventory=None,
    cauldron=None,
    potionType=None,
    objective=PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE,
    starLevel=None,
    tier=None,
):
    # Validate completeness of parameters
    assertProblemIsComplete(
        ingredientInventory=ingredientInventory,
        cauldron=cauldron,
        potionType=potionType,
        objective=objective,
        starLevel=starLevel,
        tier=tier,
    )

    result = None
    if objective == PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE:
        result = getBestPotion(
            ingredientInventory=ingredientInventory,
            cauldron=cauldron,
            potionType=potionType,
            objective=objective,
        )
    elif objective == PotionOptimizationObjective.CHEAPEST_FOR_GIVEN_STARS:
        result = getBestPotion(
            ingredientInventory=ingredientInventory,
            cauldron=cauldron,
            potionType=potionType,
            objective=objective,
            starLevel=starLevel,
        )
    elif objective == PotionOptimizationObjective.MOST_PROFITABLE_BATCH:
        result = getBestPotion(
            ingredientInventory=ingredientInventory,
            cauldron=cauldron,
            potionType=potionType,
            objective=objective,
        )
    #  print(result)


initialInventory = pd.DataFrame.from_dict(
    {
        PotionIngredient.SACK_OF_SLIME: 13,
        PotionIngredient.MANDRAKE_ROOT: 17,
        PotionIngredient.IMPSTOOL_MUSHROOM: 5,
        PotionIngredient.ROTFLY_LARVA: 15,
        PotionIngredient.SERPENTS_SLIPPERY_TONGUE: 13,
        PotionIngredient.RIVER_CALAMARI: 11,
        PotionIngredient.RIVER_PIXIES_SHELL: 5,
        PotionIngredient.FEYBERRY: 14,
        PotionIngredient.TROLLSTOOL_MUSHROOM: 2,
        PotionIngredient.RAVENS_SHADOW: 4,
        PotionIngredient.BOG_BEET: 2,
        PotionIngredient.DESERT_METAL: 0,
        PotionIngredient.GHOSTLIGHT_BLOOM: 4,
        PotionIngredient.SACK_OF_HIVE_SLIME: 0,
        PotionIngredient.LEECH_SNAILS_SHELL: 0,
        PotionIngredient.GLASS_ORE: 0,
        PotionIngredient.FIGMENT_POMME: 5,
        PotionIngredient.KAPPA_PHEROMONES: 9,
        PotionIngredient.PUCKBERRY: 5,
        PotionIngredient.GOLEMITE: 5,
        PotionIngredient.CUBIC_OOZE: 5,
        PotionIngredient.MURKWATER_PEARL: 2,
        PotionIngredient.PIXIEDUST_DIAMOND: 5,
        PotionIngredient.SPHINX_FLEA: 3,
        PotionIngredient.BUBBLE_OOZE: 2,
        PotionIngredient.SQUID_VINE: 3,
        PotionIngredient.MANDRAGON_ROOT: 8,
        PotionIngredient.MALACHITE_ORE: 4,
        PotionIngredient.GOLEMS_EYE_DIAMOND: 3,
        PotionIngredient.ABYSSALITE: 2,
        PotionIngredient.DWARF_KRAKEN: 1,
        PotionIngredient.FAIRY_FLOWER_BLOOM: 1,
        PotionIngredient.BARGHAST_CANINE: 1,
        PotionIngredient.ROTFLY_ADULT: 1,
        PotionIngredient.WARG_PHEROMONES: 3,
        PotionIngredient.GIANTSTOOL_MUSHROOM: 1,
    },
    orient="index",
    columns=["quantity"],
)

sandbox = pd.DataFrame.from_dict(
    {i: 99 for i in PotionIngredient},
    orient="index",
    columns=["quantity"],
)

special_sandbox = pd.DataFrame.from_dict(
    {
        i: 99
        for i in PotionIngredient
        if ingredientData[i]["zone"]
        in [
            "Enchanted Forest",
            "Mushroom Mire",
            "Bone Wastes",
            # "Storm Plains",
            # "Ocean Coast",
            # "Shadow Steppe",
        ]
        and ingredientData[i]["rarity"] <= 4
    },
    orient="index",
    columns=["quantity"],
)

# print(initialInventory)

# getOptimumPotionRecipe(
#     ingredientInventory=special_sandbox,
#     cauldron=Cauldron.MUDPACK_CAULDRON_I,
#     potionType=PotionType.HEALTH_POTION,
#     objective=PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE,
# )

getOptimumPotionRecipe(
    ingredientInventory=special_sandbox,
    cauldron=Cauldron.CRYSTAL_CAULDRON_III,
    potionType=PotionType.HEALTH_POTION,
    objective=PotionOptimizationObjective.MOST_PROFITABLE_BATCH,
    starLevel=6,
)

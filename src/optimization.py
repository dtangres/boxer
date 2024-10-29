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
)


class PotionOptimizationObjective(Enum):
    BEST_FOR_GIVEN_TYPE = 1
    CHEAPEST_FOR_GIVEN_STARS = 2


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
    objective=None,
    stability=PotionStability.PERFECT,
):
    # Declare maximization problem
    prob = LpProblem("Best Potion", LpMaximize)

    # Convert inventory dataframe to LpVariables
    inventoryVariables = {
        index: LpVariable(
            f"Ingredient_{index.name}",
            cat="Integer",
            lowBound=0,
            upBound=min(
                series["quantity"], cauldronProperties.loc[cauldron]["maxIngredients"]
            ),
        )
        for index, series in ingredientInventory.iterrows()
        if series["quantity"] > 0
    }

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
    tolerance = stability.value

    ratioSum = potionRatios.loc[potionType].sum()

    # Normalize potion ratios to sum to 1
    magiminRatioA = potionRatios.loc[potionType]["A"] / ratioSum
    magiminRatioB = potionRatios.loc[potionType]["B"] / ratioSum
    magiminRatioC = potionRatios.loc[potionType]["C"] / ratioSum
    magiminRatioD = potionRatios.loc[potionType]["D"] / ratioSum
    magiminRatioE = potionRatios.loc[potionType]["E"] / ratioSum

    # Specify constraints on ratio deviance
    magiminALowerBound = magiminAmount_A >= totalMagimins * max(
        0, (magiminRatioA - tolerance / 2)
    )
    magiminAUpperBound = magiminAmount_A <= totalMagimins * min(
        1, (magiminRatioA + tolerance / 2)
    )
    magiminBLowerBound = magiminAmount_B >= totalMagimins * max(
        0, (magiminRatioB - tolerance / 2)
    )
    magiminBUpperBound = magiminAmount_B <= totalMagimins * min(
        1, (magiminRatioB + tolerance / 2)
    )
    magiminCLowerBound = magiminAmount_C >= totalMagimins * max(
        0, (magiminRatioC - tolerance / 2)
    )
    magiminCUpperBound = magiminAmount_C <= totalMagimins * min(
        1, (magiminRatioC + tolerance / 2)
    )
    magiminDLowerBound = magiminAmount_D >= totalMagimins * max(
        0, (magiminRatioD - tolerance / 2)
    )
    magiminDUpperBound = magiminAmount_D <= totalMagimins * min(
        1, (magiminRatioD + tolerance / 2)
    )
    magiminELowerBound = magiminAmount_E >= totalMagimins * max(
        0, (magiminRatioE - tolerance / 2)
    )
    magiminEUpperBound = magiminAmount_E <= totalMagimins * min(
        1, (magiminRatioE + tolerance / 2)
    )

    for i in "ABCDE":
        for j in ["Upper", "Lower"]:
            prob += eval(f"magimin{i}{j}Bound")

    magiminOff_A = LpVariable(
        "magiminDeviance_A",
        lowBound=0,
        upBound=cauldronProperties.loc[cauldron]["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_A >= totalMagimins * magiminRatioA - magiminAmount_A
    prob += magiminOff_A >= magiminAmount_A - totalMagimins * magiminRatioA
    magiminOff_B = LpVariable(
        "magiminDeviance_B",
        lowBound=0,
        upBound=cauldronProperties.loc[cauldron]["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_B >= totalMagimins * magiminRatioB - magiminAmount_B
    prob += magiminOff_B >= magiminAmount_B - totalMagimins * magiminRatioB
    magiminOff_C = LpVariable(
        "magiminDeviance_C",
        lowBound=0,
        upBound=cauldronProperties.loc[cauldron]["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_C >= totalMagimins * magiminRatioC - magiminAmount_C
    prob += magiminOff_C >= magiminAmount_C - totalMagimins * magiminRatioC
    magiminOff_D = LpVariable(
        "magiminDeviance_D",
        lowBound=0,
        upBound=cauldronProperties.loc[cauldron]["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_D >= totalMagimins * magiminRatioD - magiminAmount_D
    prob += magiminOff_D >= magiminAmount_D - totalMagimins * magiminRatioD
    magiminOff_E = LpVariable(
        "magiminDeviance_E",
        lowBound=0,
        upBound=cauldronProperties.loc[cauldron]["maxMagimins"],
        cat="Integer",
    )
    prob += magiminOff_E >= totalMagimins * magiminRatioE - magiminAmount_E
    prob += magiminOff_E >= magiminAmount_E - totalMagimins * magiminRatioE

    totalDeviance = lpSum(
        [magiminOff_A, magiminOff_B, magiminOff_C, magiminOff_D, magiminOff_E]
    )
    prob += totalDeviance <= totalMagimins / 2

    # Specify cauldron constraints
    prob += totalMagimins <= cauldronProperties.loc[cauldron]["maxMagimins"]
    prob += (
        lpSum(inventoryVariables.values())
        <= cauldronProperties.loc[cauldron]["maxIngredients"]
    )

    prob += totalMagimins
    prob.solve()
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
    print(
        f"{totalDeviance.value()=}",
        f"({100 - round(totalDeviance.value() / totalMagimins.value()*100,2)}% stable)",
    )
    # print("Base star value:", sum(i.value() for i in potionStarVariables))
    # print(f"{[i.value() for i in magiminStars]=}", sum(i.value() for i in magiminStars))
    # print([i.value() for i in potionStarConstraints[:6]])
    # print(sum((i + 1) * j.value() for i, j in enumerate(magiminStars)))
    return prob


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
    #  print(result)


initialInventory = pd.DataFrame.from_dict(
    {
        PotionIngredient.SACK_OF_SLIME: 15,
        PotionIngredient.MANDRAKE_ROOT: 10,
        PotionIngredient.IMPSTOOL_MUSHROOM: 5,
        PotionIngredient.ROTFLY_LARVA: 16,
        PotionIngredient.SERPENTS_SLIPPERY_TONGUE: 14,
        PotionIngredient.RIVER_CALAMARI: 13,
        PotionIngredient.RIVER_PIXIES_SHELL: 6,
        PotionIngredient.FEYBERRY: 15,
        PotionIngredient.TROLLSTOOL_MUSHROOM: 4,
        PotionIngredient.RAVENS_SHADOW: 5,
        PotionIngredient.BOG_BEET: 3,
        PotionIngredient.DESERT_METAL: 6,
        PotionIngredient.GHOSTLIGHT_BLOOM: 5,
        PotionIngredient.SACK_OF_HIVE_SLIME: 6,
        PotionIngredient.LEECH_SNAILS_SHELL: 6,
        PotionIngredient.GLASS_ORE: 6,
        PotionIngredient.FIGMENT_POMME: 2,
        PotionIngredient.KAPPA_PHEROMONES: 8,
        PotionIngredient.PUCKBERRY: 1,
        PotionIngredient.GOLEMITE: 2,
        PotionIngredient.CUBIC_OOZE: 2,
        PotionIngredient.MURKWATER_PEARL: 1,
        PotionIngredient.PIXIEDUST_DIAMOND: 6,
    },
    orient="index",
    columns=["quantity"],
)

# print(initialInventory)

getOptimumPotionRecipe(
    ingredientInventory=initialInventory,
    cauldron=Cauldron.GLASS_CAULDRON_I,
    potionType=PotionType.HEALTH_POTION,
    objective=PotionOptimizationObjective.BEST_FOR_GIVEN_TYPE,
)

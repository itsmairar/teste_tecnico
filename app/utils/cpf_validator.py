def is_valid_cpf(cpf: str) -> bool:

    cpf_digits = [c for c in cpf if c.isdigit()]
    if len(cpf_digits) != 11:
        return False

    if cpf_digits.count(cpf_digits[0]) == 11:
        return False

    nums = list(map(int, cpf_digits))

    def calc_digit(factors: list[int]) -> int:
        s = sum(d * f for d, f in zip(nums, factors))
        mod = s % 11
        return 0 if mod < 2 else 11 - mod

    first = calc_digit(list(range(10, 1, -1)))
    nums.append(first)
    second = calc_digit(list(range(11, 1, -1)))

    return nums[9] == first and nums[10] == second

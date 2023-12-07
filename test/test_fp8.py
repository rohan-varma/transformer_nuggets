import pytest
import torch

from transformer_nuggets.fp8.scaled_quant import scaled_quant


def eager_scaled_quant(a, scale, abs_max, fp8_dtype, saturated=False):
    out = a * scale
    if saturated:
        out = torch.where(out > torch.finfo(fp8_dtype).max, torch.finfo(fp8_dtype).max, out)
        out = torch.where(
            out < -1 * torch.finfo(fp8_dtype).max, -1 * torch.finfo(fp8_dtype).max, out
        )
    return out.to(fp8_dtype), torch.max(torch.abs(out))


@pytest.mark.parametrize("fp8_dtype", [torch.float8_e4m3fn, torch.float8_e5m2])
def test_basic_quant(fp8_dtype):
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    a = torch.rand(2**12, 2**12, dtype=torch.float32, device="cuda") * 9.6
    scale = torch.tensor([4.0], dtype=torch.float32, device="cuda")
    abs_max = torch.tensor([-1.0], dtype=torch.float32, device="cuda")
    output = scaled_quant(a, scale, abs_max, fp8_dtype)
    torch.testing.assert_close(output, (a * scale).to(fp8_dtype))
    torch.testing.assert_close(abs_max, torch.tensor([9.6], dtype=torch.float32, device="cuda"))


@pytest.mark.parametrize("fp8_dtype", [torch.float8_e4m3fn, torch.float8_e5m2])
def test_saturated(fp8_dtype):
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    a = torch.rand(2**12, 2**12, dtype=torch.float32, device="cuda")
    a[0, :100] = torch.finfo(fp8_dtype).max + 100
    scale = torch.tensor([4.0], dtype=torch.float32, device="cuda")
    abs_max = torch.tensor([-1.0], dtype=torch.float32, device="cuda")
    output = scaled_quant(a, scale, abs_max, fp8_dtype, saturated=True)
    eager_output, eager_abs_max = eager_scaled_quant(a, scale, abs_max, fp8_dtype, saturated=True)
    torch.testing.assert_close(output, eager_output)
    torch.testing.assert_close(
        abs_max,
        torch.tensor([torch.finfo(fp8_dtype).max + 100], dtype=torch.float32, device="cuda"),
    )


if __name__ == "__main__":
    pytest.main([__file__])
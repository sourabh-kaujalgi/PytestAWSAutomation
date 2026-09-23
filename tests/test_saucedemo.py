import pytest

BASE_URL = "https://www.saucedemo.com/"


def login(page, username="standard_user", password="secret_sauce"):
    page.goto(BASE_URL)
    page.locator("[data-test='username']").fill(username)
    page.locator("[data-test='password']").fill(password)
    page.locator("[data-test='login-button']").click()


def test_valid_login(page, screenshot_on_failure):
    login(page)
    assert "inventory.html" in page.url


def test_invalid_login(page, screenshot_on_failure):
    login(page, "invalid_user", "wrong_password")
    assert page.locator("[data-test='error']").is_visible()


def test_locked_out_user(page, screenshot_on_failure):
    login(page, "locked_out_user", "secret_sauce")
    assert "locked out" in page.locator("[data-test='error']").inner_text().lower()


def test_inventory_products_displayed(page, screenshot_on_failure):
    login(page)

    products = page.locator("[data-test='inventory-item']")

    assert products.count() == 6


def test_add_product_to_cart(page, screenshot_on_failure):
    login(page)

    page.locator(
        "[data-test='add-to-cart-sauce-labs-backpack']"
    ).click()

    assert page.locator(
        "[data-test='shopping-cart-badge']"
    ).inner_text() == "1"


def test_remove_product_from_cart(page, screenshot_on_failure):
    login(page)

    page.locator(
        "[data-test='add-to-cart-sauce-labs-backpack']"
    ).click()

    page.locator(
        "[data-test='remove-sauce-labs-backpack']"
    ).click()

    assert page.locator(
        "[data-test='shopping-cart-badge']"
    ).count() == 0


def test_cart_contains_added_product(page, screenshot_on_failure):
    login(page)

    page.locator(
        "[data-test='add-to-cart-sauce-labs-bike-light']"
    ).click()

    page.locator(
        "[data-test='shopping-cart-link']"
    ).click()

    product_name = page.locator(
        "[data-test='inventory-item-name']"
    ).first.inner_text()

    assert product_name == "Sauce Labs Bike Light"


def test_checkout_validation(page, screenshot_on_failure):
    login(page)

    page.locator(
        "[data-test='add-to-cart-sauce-labs-backpack']"
    ).click()

    page.locator(
        "[data-test='shopping-cart-link']"
    ).click()

    page.locator(
        "[data-test='checkout']"
    ).click()

    page.locator(
        "[data-test='continue']"
    ).click()

    assert page.locator(
        "[data-test='error']"
    ).is_visible()


def test_complete_checkout(page, screenshot_on_failure):
    login(page)

    page.locator(
        "[data-test='add-to-cart-sauce-labs-backpack']"
    ).click()

    page.locator(
        "[data-test='shopping-cart-link']"
    ).click()

    page.locator(
        "[data-test='checkout']"
    ).click()

    page.locator(
        "[data-test='firstName']"
    ).fill("Sourabh")

    page.locator(
        "[data-test='lastName']"
    ).fill("QA")

    page.locator(
        "[data-test='postalCode']"
    ).fill("411057")

    page.locator(
        "[data-test='continue']"
    ).click()

    finish_button = page.locator(
        "[data-test='finish']"
    )

    assert finish_button.is_visible()

    finish_button.click()

    assert page.locator(
        "[data-test='complete-header']"
    ).inner_text() == "Thank you for your order!"


def test_product_sort_low_to_high(page, screenshot_on_failure):
    login(page)

    page.locator(
        "[data-test='product-sort-container']"
    ).select_option("lohi")

    prices = page.locator(
        "[data-test='inventory-item-price']"
    ).all_inner_texts()

    numeric_prices = [
        float(price.replace("$", ""))
        for price in prices
    ]

    assert numeric_prices == sorted(numeric_prices)


def test_logout(page, screenshot_on_failure):
    login(page)

    page.locator(
        "[data-test='open-menu']"
    ).click()

    page.locator(
        "[data-test='logout-sidebar-link']"
    ).click()

    assert page.locator(
        "[data-test='login-button']"
    ).is_visible()
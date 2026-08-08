import pytest

BASE_URL = "https://www.saucedemo.com/"


def login(page, username="standard_user", password="secret_sauce"):
    page.goto(BASE_URL)
    page.locator("#user-name").fill(username)
    page.locator("#password").fill(password)
    page.locator("#login-button").click()


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
    assert page.locator(".inventory_item").count() == 6


def test_add_product_to_cart(page, screenshot_on_failure):
    login(page)
    page.locator("[data-test='add-to-cart-sauce-labs-backpack']").click()
    assert page.locator(".shopping_cart_badge").inner_text() == "1"


def test_remove_product_from_cart(page, screenshot_on_failure):
    login(page)
    page.locator("[data-test='add-to-cart-sauce-labs-backpack']").click()
    page.locator("[data-test='remove-sauce-labs-backpack']").click()
    assert page.locator(".shopping_cart_badge").count() == 0


def test_cart_contains_added_product(page, screenshot_on_failure):
    login(page)
    page.locator("[data-test='add-to-cart-sauce-labs-bike-light']").click()
    page.locator(".shopping_cart_link").click()
    assert page.locator(".inventory_item_name").inner_text() == "Sauce Labs Bike Light"


def test_checkout_validation(page, screenshot_on_failure):
    login(page)
    page.locator("[data-test='add-to-cart-sauce-labs-backpack']").click()
    page.locator(".shopping_cart_link").click()
    page.locator("#checkout").click()
    page.locator("#continue").click()
    assert page.locator("[data-test='error']").is_visible()


def test_complete_checkout(page, screenshot_on_failure):
    login(page)
    page.locator("[data-test='add-to-cart-sauce-labs-backpack']").click()
    page.locator(".shopping_cart_link").click()
    page.locator("#checkout").click()

    page.locator("#first-name").fill("Sourabh")
    page.locator("#last-name").fill("QA")
    page.locator("#postal-code").fill("411057")
    page.locator("#continue").click()

    assert page.locator("#finish").is_visible()

    page.locator("#finish").click()

    assert page.locator(".complete-header").inner_text() == "Thank you for your order!"


def test_product_sort_low_to_high(page, screenshot_on_failure):
    login(page)
    page.locator(".product_sort_container").select_option("lohi")

    prices = page.locator(".inventory_item_price").all_inner_texts()
    numeric_prices = [float(p.replace("$", "")) for p in prices]

    assert numeric_prices == sorted(numeric_prices)


def test_logout(page, screenshot_on_failure):
    login(page)
    page.locator("#react-burger-menu-btn").click()
    page.locator("#logout_sidebar_link").click()

    assert page.locator("#login-button").is_visible()

import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it } from "vitest"
import { jsonResponse, mockApi, renderApp, setUpApiClient, tearDownApp } from "../../support/app"

async function fillSignupForm(password: string, email = "member@example.com") {
  await userEvent.type(await screen.findByPlaceholderText("Enter your name"), "New Member")
  await userEvent.type(screen.getByPlaceholderText("name@example.com"), email)
  await userEvent.type(screen.getByPlaceholderText("Create a password"), password)
  await userEvent.type(screen.getByPlaceholderText("Confirm your password"), password)
  await userEvent.click(screen.getByRole("button", { name: "Create Account" }))
}

describe("UserSignupForm", () => {
  beforeEach(setUpApiClient)
  afterEach(tearDownApp)

  it("submits a 12-character all-lowercase password and shows why the server rejected it", async () => {
    const api = mockApi({
      "POST /api/access/register": () => jsonResponse({ status: 400, title: "Bad Request", detail: "Password is too common." }, 400),
    })

    renderApp("/signup")
    await fillSignupForm("passwordpass")

    expect(await screen.findByText("Password is too common.")).toBeInTheDocument()
    expect(api.requestCount("POST /api/access/register")).toBe(1)
  })

  it("explains the password rules when the server rejects the sign-up without saying why", async () => {
    mockApi({
      "POST /api/access/register": () => jsonResponse({ status: 400, title: "Bad Request", detail: "The request is invalid." }, 400),
    })

    renderApp("/signup")
    await fillSignupForm("passwordpass")

    expect(
      await screen.findByText("We couldn't create your account. Use a password of 12 to 128 characters that is not your email address and not a common password."),
    ).toBeInTheDocument()
    expect(screen.queryByText("The request is invalid.")).not.toBeInTheDocument()
  })

  it("submits the email lower-cased", async () => {
    let submitted: { identifier?: string } = {}
    mockApi({
      "POST /api/access/register": async (request) => {
        submitted = await request.json()
        return jsonResponse({ id: "user-1" }, 201)
      },
    })

    const { router } = renderApp("/signup")
    await fillSignupForm("passwordpass", "New.Member@Example.COM")

    await waitFor(() => expect(router.state.location.pathname).toBe("/login"))
    expect(submitted.identifier).toBe("new.member@example.com")
  })

  it("does not submit a password shorter than 12 characters", async () => {
    const api = mockApi({})

    renderApp("/signup")
    await fillSignupForm("Sh0rt!pass")

    expect(await screen.findByText("Password must be at least 12 characters long")).toBeInTheDocument()
    expect(api.requestCount("POST /api/access/register")).toBe(0)
  })
})

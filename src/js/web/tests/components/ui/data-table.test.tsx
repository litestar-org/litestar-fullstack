import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"
import { createDataTableColumnHelper, DataTable } from "@/components/ui/data-table"

interface Member {
  name: string
  seats: number
}

const members: Member[] = Array.from({ length: 12 }, (_, index) => ({ name: `Member ${String(index + 1).padStart(2, "0")}`, seats: 12 - index }))

const helper = createDataTableColumnHelper<Member>()
const columns = helper.columns([
  helper.accessor("name", { header: "Name" }),
  helper.accessor("seats", {
    header: ({ column }) => (
      <button type="button" onClick={column.getToggleSortingHandler()}>
        Seats
      </button>
    ),
  }),
])

describe("DataTable", () => {
  it("pages through rows ten at a time", async () => {
    render(<DataTable columns={columns} data={members} />)

    expect(screen.getByText("12 results")).toBeInTheDocument()
    expect(screen.getByText("Member 10")).toBeInTheDocument()
    expect(screen.queryByText("Member 11")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled()

    await userEvent.click(screen.getByRole("button", { name: "Next" }))

    expect(screen.getByText("Member 11")).toBeInTheDocument()
    expect(screen.queryByText("Member 10")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled()
  })

  it("filters rows by the search column", async () => {
    render(<DataTable columns={columns} data={members} searchKey="name" searchPlaceholder="Search members" />)

    await userEvent.type(screen.getByPlaceholderText("Search members"), "member 07")

    expect(screen.getByText("1 result")).toBeInTheDocument()
    expect(screen.getByText("Member 07")).toBeInTheDocument()
    expect(screen.queryByText("Member 01")).not.toBeInTheDocument()
  })

  it("sorts rows when a sortable header is toggled", async () => {
    render(<DataTable columns={columns} data={members} />)

    await userEvent.click(screen.getByRole("button", { name: "Seats" }))
    await userEvent.click(screen.getByRole("button", { name: "Seats" }))

    const firstDataRow = screen.getAllByRole("row")[1]
    expect(firstDataRow).toHaveTextContent("Member 12")
  })

  it("shows the empty message when there are no rows", () => {
    render(<DataTable columns={columns} data={[]} emptyMessage="No members yet." />)

    expect(screen.getByText("No members yet.")).toBeInTheDocument()
  })
})

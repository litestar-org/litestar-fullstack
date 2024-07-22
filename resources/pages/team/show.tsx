import DeleteUserForm from "@/pages/profile/partials/delete-user-form"
import UpdatePasswordForm from "@/pages/profile/partials/update-password-form"
import UpdateProfileInformationForm from "@/pages/profile/partials/update-profile-information-form"
import { AppLayout } from "@/layouts/app-layout"
import { Container } from "@/components/container"
import { Head } from "@inertiajs/react"
import { Header } from "@/components/header"

interface Props {
  mustVerifyEmail: boolean
  status?: string
}

const title = "Team Home"
export default function Show({ mustVerifyEmail, status }: Props) {
  return (
    <>
      <Head title={title} />
      <Header title={title} />
      <Container>
        <div className="max-w-3xl space-y-6">
          <UpdateProfileInformationForm
            mustVerifyEmail={mustVerifyEmail}
            status={status}
          />
          <UpdatePasswordForm />
          <DeleteUserForm />
        </div>
      </Container>
    </>
  )
}

Show.layout = (page: any) => <AppLayout children={page} />

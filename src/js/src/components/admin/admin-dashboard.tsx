import { AdminTags } from "@/components/admin/admin-tags";
import { AdminUsers } from "@/components/admin/admin-users";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function AdminDashboard() {
	return (
		<div className="space-y-6">
			<Tabs defaultValue="users" className="w-full">
				<TabsList>
					<TabsTrigger value="users">Users</TabsTrigger>
					<TabsTrigger value="tags">Tags</TabsTrigger>
				</TabsList>
				<TabsContent value="users">
					<AdminUsers />
				</TabsContent>
				<TabsContent value="tags">
					<AdminTags />
				</TabsContent>
			</Tabs>
		</div>
	);
}
